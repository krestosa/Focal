#version 120

uniform sampler2D texture;

varying vec2 texcoord;
varying vec4 vertexColor;

/* DRAWBUFFERS:0 */

void main() {
    vec4 crack = texture2D(texture, texcoord) * vertexColor;
    if (crack.a < 0.01) {
        discard;
    }

    gl_FragData[0] = crack;
}
