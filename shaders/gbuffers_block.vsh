#version 150 compatibility

out vec2 focalTexCoord;
out vec2 focalLightCoord;
out vec4 focalVertexColor;

void main() {
    gl_Position = gl_ModelViewProjectionMatrix * gl_Vertex;
    focalTexCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    focalLightCoord = (gl_TextureMatrix[1] * gl_MultiTexCoord1).xy;
    focalVertexColor = gl_Color;
}
