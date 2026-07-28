#version 150

out vec2 cloudTexCoord;
out vec4 cloudColor;

void main() {
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
    cloudTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    cloudColor = gl_Color;
}
