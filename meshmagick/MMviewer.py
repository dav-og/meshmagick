#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module is part of meshmagick. It implements a viewer based on vtk
"""

import vtk

class MMViewer:
    def __init__(self):

        # Building renderer
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.7706, 0.8165, 1.0)

        # Building render window
        self.render_window = vtk.vtkRenderWindow()
        # self.render_window.SetSize(1024, 769)
        self.render_window.FullScreenOn()
        self.render_window.SetWindowName("Meshmagick viewer")
        self.render_window.AddRenderer(self.renderer)

        # Building interactor
        self.render_window_interactor = vtk.vtkRenderWindowInteractor()
        self.render_window_interactor.SetRenderWindow(self.render_window)
        self.render_window_interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.render_window_interactor.SetStillUpdateRate(0.0001)

        # keyPressCallback = vtk.vtkCommand()
        self.render_window_interactor.AddObserver('KeyPressEvent', self.KeyPress, 0.0)

        # Building axes view
        axes = vtk.vtkAxesActor()
        widget = vtk.vtkOrientationMarkerWidget()
        widget.SetOrientationMarker(axes)
        self.widget = widget

        # Building command annotations
        command_text = "left mouse : rotate\n" + \
                        "right mouse : zoom\n" + \
                        "middle mouse : pan\n" + \
                        "ctrl+left mouse : spin\n" + \
                        "n : show normals\n" + \
                        "b : show axes box\n" + \
                        "f : focus on the mouse cursor\n" + \
                        "r : reset view\n" + \
                        "s : surface representation\n" + \
                        "w : wire representation\n" + \
                        "e : quit"

        corner_annotation = vtk.vtkCornerAnnotation()
        corner_annotation.SetLinearFontScaleFactor(2)
        corner_annotation.SetNonlinearFontScaleFactor(1)
        corner_annotation.SetMaximumFontSize(20)
        corner_annotation.SetText(3, command_text)
        corner_annotation.GetTextProperty().SetColor(0., 0., 0.)
        self.renderer.AddViewProp(corner_annotation)

        self.normals = []
        self.axes = []

        self.polydatas = list()

    def normals_on(self):
        self.normals = True

    def normals_off(self):
        self.normals = False

    def add_polydata(self, polydata):
        if not isinstance(polydata, vtk.vtkPolyData):
            raise AssertionError, 'polydata must be a vtkPolyData object'

        self.polydatas.append(polydata)

        # Building mapper
        mapper = vtk.vtkPolyDataMapper()
        if vtk.VTK_MAJOR_VERSION <= 5:
            mapper.SetInput(polydata)
        else:
            mapper.SetInputData(polydata)

        # Building actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # Properties setting
        actor.GetProperty().SetColor(1, 1, 0)
        actor.GetProperty().EdgeVisibilityOn()
        actor.GetProperty().SetEdgeColor(0, 0, 0)
        actor.GetProperty().SetLineWidth(1)

        self.renderer.AddActor(actor)

    def show_normals(self):
        for polydata in self.polydatas:
            normals = vtk.vtkPolyDataNormals()
            normals.ConsistencyOff()
            # normals.ComputePointNormalsOn()
            normals.ComputeCellNormalsOn()
            if vtk.VTK_MAJOR_VERSION <= 5:
                normals.SetInput(polydata)
            else:
                normals.SetInputData(polydata)
            normals.Update()

            normals_at_centers = vtk.vtkCellCenters()
            normals_at_centers.SetInputConnection(normals.GetOutputPort())

            normals_mapper = vtk.vtkPolyDataMapper()
            if vtk.VTK_MAJOR_VERSION <= 5:
                normals_output = normals.GetOutput()
                normals_mapper.SetInput(normals_output)
            else:
                normals_mapper.SetInputData(normals.GetOutput())
            normals_actor = vtk.vtkActor()
            normals_actor.SetMapper(normals_mapper)

            arrows = vtk.vtkArrowSource()
            arrows.SetTipResolution(16)
            arrows.SetTipLength(0.3)
            arrows.SetTipRadius(0.1)

            glyph = vtk.vtkGlyph3D()
            glyph.SetSourceConnection(arrows.GetOutputPort())
            glyph.SetInputConnection(normals_at_centers.GetOutputPort())
            glyph.SetVectorModeToUseNormal()
            glyph.Update()

            glyph_mapper = vtk.vtkPolyDataMapper()
            glyph_mapper.SetInputConnection(glyph.GetOutputPort())

            glyph_actor = vtk.vtkActor()
            glyph_actor.SetMapper(glyph_mapper)

            self.renderer.AddActor(glyph_actor)
            self.normals.append(glyph_actor)

    def show_axes(self):

        tprop = vtk.vtkTextProperty()
        tprop.SetColor(0., 0., 0.)
        tprop.ShadowOn()

        axes = vtk.vtkCubeAxesActor2D()
        if vtk.VTK_MAJOR_VERSION <= 5:
            output = self.polydatas[0]
            axes.SetInput(output)
        else:
            axes.SetInputConnection(self.polydatas[0])
        axes.SetCamera(self.renderer.GetActiveCamera())
        axes.SetLabelFormat("%6.4g")
        axes.SetFlyModeToOuterEdges()
        axes.SetFontFactor(0.8)
        axes.SetAxisTitleTextProperty(tprop)
        axes.SetAxisLabelTextProperty(tprop)
        # axes.DrawGridLinesOn()

        self.renderer.AddViewProp(axes)
        self.axes.append(axes)


    def show(self):

        self.widget.SetInteractor(self.render_window_interactor)
        self.widget.SetEnabled(1)
        self.widget.InteractiveOn()

        self.render_window_interactor.Initialize()
        self.renderer.ResetCamera()
        self.render_window.Render()
        self.render_window_interactor.Start()

    def finalize(self):
        del self.render_window
        del self.render_window_interactor

    def KeyPress(self, obj, event):
        key = obj.GetKeySym()

        if key == 'n':
            if self.normals:
                # self.normals = False
                for actor in self.normals:
                    self.renderer.RemoveActor(actor)
                self.renderer.Render()
                self.normals = []
            else:
                self.show_normals()
                self.renderer.Render()
        elif key == 'b':
            if self.axes:
                for axis in self.axes:
                    self.renderer.RemoveActor(axis)
                self.axes = []
            else:
                self.show_axes()

        elif key == 'e' or key == 'q':
            self.render_window_interactor.GetRenderWindow().Finalize()
            self.render_window_interactor.TerminateApp()

