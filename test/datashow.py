import numpy as np
from matplotlib import pyplot as plt

x = np.arange(1, 11)
y = 2*x + 5

plt.title("demo")
plt.plot(x,y)
print("plot")
plt.show()