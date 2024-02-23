from contextlib import ExitStack
from matplotlib.axes import Axes
import matplotlib.transforms as transforms
import matplotlib.axis as maxis
import matplotlib.spines as mspines
from matplotlib.projections import register_projection
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, "../")
import util.calculator as calc
import numpy as np

# The sole purpose of this class is to look at the upper, lower, or total
# interval as appropriate and see what parts of the tick to draw, if any.
class SkewXTick(maxis.XTick):
    def draw(self, renderer):
        # When adding the callbacks with `stack.callback`, we fetch the current
        # visibility state of the artist with `get_visible`; the ExitStack will
        # restore these states (`set_visible`) at the end of the block (after
        # the draw).
        with ExitStack() as stack:
            for artist in [self.gridline, self.tick1line, self.tick2line,
                           self.label1, self.label2]:
                stack.callback(artist.set_visible, artist.get_visible())
            needs_lower = transforms.interval_contains(
                self.axes.lower_xlim, self.get_loc())
            needs_upper = transforms.interval_contains(
                self.axes.upper_xlim, self.get_loc())
            self.tick1line.set_visible(
                self.tick1line.get_visible() and needs_lower)
            self.label1.set_visible(
                self.label1.get_visible() and needs_lower)
            self.tick2line.set_visible(
                self.tick2line.get_visible() and needs_upper)
            self.label2.set_visible(
                self.label2.get_visible() and needs_upper)
            super().draw(renderer)

    def get_view_interval(self):
        return self.axes.xaxis.get_view_interval()


# This class exists to provide two separate sets of intervals to the tick,
# as well as create instances of the custom tick
class SkewXAxis(maxis.XAxis):
    def _get_tick(self, major):
        return SkewXTick(self.axes, None, major=major)

    def get_view_interval(self):
        return self.axes.upper_xlim[0], self.axes.lower_xlim[1]


# This class exists to calculate the separate data range of the
# upper X-axis and draw the spine there. It also provides this range
# to the X-axis artist for ticking and gridlines
class SkewSpine(mspines.Spine):
    def _adjust_location(self):
        pts = self._path.vertices
        if self.spine_type == 'top':
            pts[:, 0] = self.axes.upper_xlim
        else:
            pts[:, 0] = self.axes.lower_xlim


# This class handles registration of the skew-xaxes as a projection as well
# as setting up the appropriate transformations. It also overrides standard
# spines and axes instances as appropriate.
class SkewXAxes(Axes):
    # The projection must specify a name.  This will be used be the
    # user to select the projection, i.e. ``subplot(projection='skewx')``.
    name = 'skewx'

    def _init_axis(self):
        # Taken from Axes and modified to use our modified X-axis
        self.xaxis = SkewXAxis(self)
        self.spines.top.register_axis(self.xaxis)
        self.spines.bottom.register_axis(self.xaxis)
        self.yaxis = maxis.YAxis(self)
        self.spines.left.register_axis(self.yaxis)
        self.spines.right.register_axis(self.yaxis)

    def _gen_axes_spines(self):
        spines = {'top': SkewSpine.linear_spine(self, 'top'),
                  'bottom': mspines.Spine.linear_spine(self, 'bottom'),
                  'left': mspines.Spine.linear_spine(self, 'left'),
                  'right': mspines.Spine.linear_spine(self, 'right')}
        return spines

    def _set_lim_and_transforms(self):
        """
        This is called once when the plot is created to set up all the
        transforms for the data, text and grids.
        """
        rot = 30

        # Get the standard transform setup from the Axes base class
        super()._set_lim_and_transforms()

        # Need to put the skew in the middle, after the scale and limits,
        # but before the transAxes. This way, the skew is done in Axes
        # coordinates thus performing the transform around the proper origin
        # We keep the pre-transAxes transform around for other users, like the
        # spines for finding bounds
        self.transDataToAxes = (
            self.transScale
            + self.transLimits
            + transforms.Affine2D().skew_deg(rot, 0)
        )
        # Create the full transform from Data to Pixels
        self.transData = self.transDataToAxes + self.transAxes

        # Blended transforms like this need to have the skewing applied using
        # both axes, in axes coords like before.
        self._xaxis_transform = (
            transforms.blended_transform_factory(
                self.transScale + self.transLimits,
                transforms.IdentityTransform())
            + transforms.Affine2D().skew_deg(rot, 0)
            + self.transAxes
        )

    @property
    def lower_xlim(self):
        return self.axes.viewLim.intervalx

    @property
    def upper_xlim(self):
        pts = [[0., 1.], [1., 1.]]
        return self.transDataToAxes.inverted().transform(pts)[:, 0]


# Now register the projection with matplotlib so the user can select it.
register_projection(SkewXAxes)


def draw_skewt():
  trange=np.arange(-80,50,1)+273.15
  prange=np.arange(50,1001,1)
  tt,pp=np.meshgrid(trange,prange)
  es_hPa  = calc.cal_saturated_vapor_pressure(tt)
  qq, rr  = calc.cal_absolute_humidity(es_hPa, pp)
  theta   = calc.cal_potential_temperature(pp, tt)-273.15
  theta_e = calc.cal_equivalent_potential_temperature(pp,rr,tt)-273.15

  # find theta_e ticks
  idxp1000=np.where(prange==1000)[0][0]
  idxp700=np.where(prange==700)[0][0]
  idxt=np.where(np.isin(trange-273.15,[8,12,16,20,24,28,32]))[0]
  ticks_thetae=theta_e[(idxp1000*np.ones(idxt.size)).astype(int),idxt]
  # find theta ticks
  ticks_theta=np.arange(-30,201,20)

  plt.rcParams.update({'font.size':13,
      'savefig.facecolor':(1,1,1,0),
      'axes.linewidth':2,
      'lines.linewidth':3}
  )
  # Create a new figure. The dimensions here give a good aspect ratio
  fig = plt.figure(figsize=(6.5875, 6.2125*1.2))
  ax = fig.add_axes([0.15,0.07,0.7,0.85],projection='skewx')

  # plot grid
  plt.grid(True,axis='y')
  for t in np.arange(-100,100,20):
    plt.fill_betweenx([1,1050],x1=t,x2=t+10,color='0.8')

  # plot adiabatic line and qv line
  plt.contour(trange-273.15, prange, theta,\
              levels = ticks_theta, colors = '#E8100C',\
              linewidths = 0.5, linestyles='-')
  plt.contour(trange-273.15, prange, theta_e,\
              levels = ticks_thetae, colors = '#4BAB4E',\
              linewidths = 0.5, linestyles = '-')
  C1 = plt.contour(trange[:]-273.15, prange[idxp700:idxp1000], qq[idxp700:idxp1000,:]*1e3,\
                   levels = [1,2,3,5,8,12,20], colors = 'k',\
                   linewidths = 0.5, linestyles=':')
  plt.yscale('log')
  plt.ylim(1000,100)
  return fig, ax

