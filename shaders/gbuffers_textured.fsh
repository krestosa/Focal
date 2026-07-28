#version 330 compatibility

uniform sampler2D texture;

in vec2 focalTexCoord;
in vec4 focalVertexColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 focalColor;

void main() {
    vec4 albedo = texture2D(texture, focalTexCoord) * focalVertexColor;
    if (albedo.a < 0.1) {
        discard;
    }
    focalColor = albedo;
}
