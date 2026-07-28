#version 150 compatibility

uniform sampler2D texture;
uniform sampler2D lightmap;

in vec2 texcoord;
in vec2 lightcoord;
in vec4 vertexColor;

/* DRAWBUFFERS:0 */
layout(location = 0) out vec4 outColor;

void main() {
    vec4 albedo = texture2D(texture, texcoord) * vertexColor;
    if (albedo.a <= 0.0039215686) {
        discard;
    }

    vec3 vanillaLight = texture2D(lightmap, lightcoord).rgb;
    outColor = vec4(albedo.rgb * vanillaLight, albedo.a);
}
