#version 120

uniform sampler2D texture;
uniform sampler2D lightmap;

varying vec2 texcoord;
varying vec2 lightcoord;
varying vec4 vertexColor;

/* DRAWBUFFERS:0 */

void main() {
    vec4 albedo = texture2D(texture, texcoord) * vertexColor;
    if (albedo.a < 0.5) {
        discard;
    }

    vec3 lighting = texture2D(lightmap, lightcoord).rgb;
    gl_FragData[0] = vec4(albedo.rgb * lighting, albedo.a);
}
