#version 330 compatibility

out vec4 focalSkyColor;

void main() {
    gl_Position = ftransform();
    focalSkyColor = gl_Color;
}
