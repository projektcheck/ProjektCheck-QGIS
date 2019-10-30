from argparse import ArgumentParser
import matplotlib.pyplot as plt
plt.rcdefaults()
from pickle import load
import os

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('-f', '--file', dest='file',
                        help='File with pickled plot axes')

    parser.add_argument('-t', '--title', dest='title',
                        help='Window title')
    options = parser.parse_args()
    with open(options.file, 'r') as f:
        axes = load(f)
    # workaround in older matplotlib versions,
    # callbacks are not correctly pickled/unpickled
    axes.figure.callbacks.callbacks = {}
    # override default name as it takes title by default but can't handle
    # Umlaute
    axes.figure.canvas.get_default_filename = lambda: 'Diagramm.png'
    axes.figure.canvas.set_window_title(options.title)
    axes.title.set_position([.5, 1.05])
    plt.show()
    os.remove(options.file)
