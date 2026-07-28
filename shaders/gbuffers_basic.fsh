#version 330 compatibility

in vec4 focalVertexColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 focalColor;

void main() {
    focalColor = focalVertexColor;
}
