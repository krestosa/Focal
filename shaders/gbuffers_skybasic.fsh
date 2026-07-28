#version 330 compatibility

in vec4 focalSkyColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 focalColor;

void main() {
    focalColor = focalSkyColor;
}
