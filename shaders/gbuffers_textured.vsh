#version 330 compatibility

out vec2 focalTexCoord;
out vec4 focalVertexColor;

void main() {
    gl_Position = ftransform();
    focalTexCoord = gl_MultiTexCoord0.xy;
    focalVertexColor = gl_Color;
}
