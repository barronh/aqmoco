def daymean(x):
    axis = 0
    shape = list(x.shape)
    shape[axis] = -1
    shape.insert(axis + 1, 24)
    return x.reshape(*shape).mean(1)
