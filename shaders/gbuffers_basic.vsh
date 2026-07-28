#version 330 compatibility

out vec4 focalVertexColor;

void main() {
    gl_Position = ftransform();
    focalVertexColor = gl_Color;
}
