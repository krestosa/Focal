#version 330 compatibility

out vec2 focalTexcoord;
out vec2 focalLightcoord;
out vec4 focalVertexColor;

void main() {
    gl_Position = ftransform();
    focalTexcoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    focalLightcoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    focalVertexColor = gl_Color;
}
