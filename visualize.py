#!/usr/bin/env python

import sys
import numpy as np
import json
import math
from PIL import Image
from glumpy import app, gl, glm, gloo, data, key
from glumpy import transforms

import model
import render

window = app.Window(color=(0.30, 0.30, 0.35, 1.00))

view = np.eye(4, dtype=np.float32)
projection = np.eye(4, dtype=np.float32)

load = lambda name: np.array(Image.open(name))
cubemap = np.stack([
    load("cube/pos_x.png"),
    load("cube/neg_x.png"),
    load("cube/pos_y.png"),
    load("cube/neg_y.png"),
    load("cube/pos_z.png"),
    load("cube/neg_z.png"),
], axis=0).view(gloo.TextureCube)
cube = render.CubemapCube(cubemap)

m = model.load_model(sys.argv[1])
element = render.Element(m["elements"][0], m["textures"])
mmm = render.Model(m)

views = ["perspective", "ortho", "fake_ortho"]
view_index = 0

rotations = ["top-left", "top-right", "bottom-right", "bottom-left"]
rotation_index = 0

model, view, projection = None, None, None

first_render = True
run_phi = False
phi = 45

@window.event
def on_draw(dt):
    global first_render, phi, model, view, projection

    window.clear()
    w, h = window.get_size()

    if model is None:
        aspect = w / h
        v = views[view_index]

        if v == "perspective":
            model, view, projection = render.create_transform_perspective(aspect=aspect)
        elif v == "ortho":
            model, view, projection = render.create_transform_ortho(aspect=aspect, fake_ortho=False)
        elif v == "fake_ortho":
            model, view, projection = render.create_transform_ortho(aspect=aspect, fake_ortho=True)
        else:
            assert False, "Invalid view type '%s'" % view

    texture = None
    fbo = None
    if first_render:
        w, h = 32, 32
        texture = np.zeros((h, w, 4), dtype=np.uint8).view(gloo.Texture2D)
        depth = np.zeros((h, w), dtype=np.float32).view(gloo.DepthTexture)
        fbo = gloo.FrameBuffer(color=[texture], depth=depth)
        fbo.activate()

        projection = glm.ortho(-1, 1, -1, 1, 2.0, 50.0)
        glm.scale(projection, 1.0, -1.0, 1.0)

        gl.glViewport(0, 0, w, h)
        gl.glClearColor(0.0, 0.0, 0.0, 0.0)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)
        gl.glEnable(gl.GL_DEPTH_TEST)

    rotation = rotation_index
    if run_phi:
        phi += 0.2
    actual_model = np.dot(render.create_model_transform(rotation, phi), model)
    mmm.render(actual_model, view, projection)

    if first_render:
        image = Image.fromarray(texture.get())
        image.save("block.png")
        fbo.deactivate()
        first_render = False

@window.event
def on_resize(width, height):
    global model, view, projection
    model, view, projection = None, None, None

@window.event
def on_key_press(code, mod):
    global view_index, model, view, projection, rotation_index, run_phi

    if code == ord("V"):
        view_index = (view_index + 1) % len(views)
        model, view, projection = None, None, None

    if code == key.LEFT:
        rotation_index = (rotation_index - 1) % len(rotations)

    if code == key.RIGHT:
        rotation_index = (rotation_index + 1) % len(rotations)

    if code == key.SPACE:
        run_phi = not run_phi

    if code == ord("Q"):
        window.close()

@window.event
def on_init():
    gl.glEnable(gl.GL_DEPTH_TEST)
    gl.glDepthFunc(gl.GL_LESS)

    #gl.glEnable(gl.GL_CULL_FACE)
    
    gl.glEnable(gl.GL_BLEND)
    gl.glBlendEquationSeparate(gl.GL_FUNC_ADD, gl.GL_FUNC_ADD)
    gl.glBlendFuncSeparate(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA, gl.GL_ONE, gl.GL_ONE_MINUS_SRC_ALPHA)

app.run()
