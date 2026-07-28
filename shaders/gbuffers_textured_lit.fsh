#version 330 compatibility

uniform sampler2D texture;
uniform sampler2D lightmap;

in vec2 focalTexCoord;
in vec2 focalLightCoord;
in vec4 focalVertexColor;

/* RENDERTARGETS: 0 */
layout(location = 0) out vec4 focalColor;

void main() {
    vec4 albedo = texture2D(texture, focalTexCoord) * focalVertexColor;
    if (albedo.a < 0.1) {
        discard;
    }

    vec3 vanillaLight = texture2D(lightmap, focalLightCoord).rgb;
    focalColor = vec4(albedo.rgb * vanillaLight, albedo.a);
}
