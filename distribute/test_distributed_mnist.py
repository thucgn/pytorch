# coding=utf-8
# pylint: skip-file

# pylint: disable-all

import os
import time
import torch
import math
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import torch.distributed as dist
import torchvision.datasets as datasets
import torchvision.transforms as transforms
from progress import accuracy
from random import Random
from torch.multiprocessing import Process
from test import Net

class Partition(object):
    def __init__(self, data, index):
        self.data = data
        self.index = index

    def __len__(self):
        return len(self.index)

    def __getitem__(self, index):
        data_idx = self.index[index]
        return self.data[data_idx]


class DataPartitioner(object):
    def __init__(self, data, sizes=(0.7, 0.2, 0.1), seed=1234):
        self.data = data
        self.partitions = []
        rng = Random()
        rng.seed(seed)
        data_len = len(data)
        indexes = [ x for x in range(0, data_len) ]
        rng.shuffle(indexes)

        parts = [ int(data_len*x) for x in sizes[0:-1] ]
        # set the last part to rest data
        remain = data_len
        for x in parts:
            data_len -= x
        parts.append(remain)

        accum = 0
        for x in parts:
            self.partitions.append(indexes[accum:accum+x])
            accum += x

    def use(self, partition):
        return Partition(self.data, self.partitions[partition])


def paritition_dataset():
    dataset = datasets.MNIST('./data', train=True, download=True,
            transform=transforms.Compose([
                transforms.ToTensor(),
                transforms.Normalize((0.1307,), (0.3081,))
                ]))
    size = dist.get_world_size()
    batch = 128/float(size)
    partition_sizes = [1.0 / size for _ in range(size)]
    partition = DataPartitioner(dataset, partition_sizes)
    partition = partition.use(dist.get_rank())

    print("rank %d partitionsize %d batchsize %d" %
            (dist.get_rank(),len(partition), batch))
    train_set = torch.utils.data.DataLoader(
            partition,
            batch_size = int(batch),
            shuffle=True)

    return train_set, batch

def average_gradients(model):
    size = dist.get_world_size()
    for param in model.parameters():
        dist.all_reduce(param.grad.data, op=dist.ReduceOp.SUM)
        param.grad.data /= float(size)

def run(rank, size):
    torch.manual_seed(1234)
    train_set, batch = paritition_dataset()
    device = torch.device("cuda:{}".format(rank))
    model = Net().to(device)
    optimizer = optim.SGD(model.parameters(), 
            lr = 0.01, momentum=0.5)

    num_batches = math.ceil(len(train_set.dataset)/float(batch))

    for epoch in range(10):
        epoch_loss = 0.0
        for data, target in train_set:
            data = data.to(device)
            target = target.to(device)
            optimizer.zero_grad()
            output = model(data)
            loss = F.nll_loss(output, target)
            epoch_loss += loss.item()
            loss.backward()
            average_gradients(model)
            optimizer.step()
            #acc1, acc5 = accuracy(output, target, topk=(1,5))
            #print("rank %d acc1 %f acc2 %f", dist.get_rank(), 
            #        acc1, acc5)
        print('Rank ', dist.get_rank(), ', epoch ', epoch, ': ',
                    epoch_loss/num_batches)

def init_process(rank, size, fn, backend='gloo'):
    os.environ['MASTER_ADDR'] = '127.0.0.1'
    os.environ['MASTER_PORT'] = '12347'

    dist.init_process_group(backend, rank=rank, world_size=size)
    dist.barrier()
    fn(rank, size)

if __name__ == "__main__":
    size = 2
    processes = []
    func = run
    for rank in range(size):
        p = Process(target=init_process, args=(rank, size, func, "nccl"))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
