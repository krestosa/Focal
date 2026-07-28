#version 330 compatibility

uniform sampler2D gtexture;
uniform sampler2D lightmap;
uniform float alphaTestRef;

in vec2 focalTexcoord;
in vec2 focalLightcoord;
in vec4 focalVertexColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 focalColor;

void main() {
    vec4 albedo = texture(gtexture, focalTexcoord) * focalVertexColor;
    if (albedo.a < alphaTestRef) {
        discard;
    }

    vec3 vanillaLight = texture(lightmap, focalLightcoord).rgb;
    focalColor = vec4(albedo.rgb * vanillaLight, albedo.a);
}
