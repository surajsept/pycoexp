import matplotlib.pyplot as plt
import seaborn as sns

def line(df, **kwargs):
    if ('subplots' in kwargs) and ('layout' in kwargs):
        df.plot(subplots=kwargs['subplots'], layout=kwargs['layout'])
    else:
        df.plot()
    plt.tight_layout()
    return plt.show()

def heatmap(df, **kwargs):
    cmap = 'seismic'

    if 'cmap' in kwargs:
        cmap = kwargs['cmap']

    if 'vmin' in kwargs:
        vmin = kwargs['vmin']

    if 'vmax' in kwargs:
        vmax = kwargs['vmax']

    sns.heatmap(data=df)


