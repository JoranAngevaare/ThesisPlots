import thesis_plots
import matplotlib.pyplot as plt

def test_rotation_curve():
    rotation_curve = thesis_plots.RotationCurve()
    rotation_curve.plot_rotation_curve()
    plt.clf()

    rotation_curve.plot_rotation_curve_fancy()
    plt.clf()