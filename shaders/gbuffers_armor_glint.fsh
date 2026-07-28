#version 120

uniform sampler2D texture;

varying vec2 texcoord;
varying vec4 vertexColor;

/* DRAWBUFFERS:0 */

void main() {
    vec4 glint = texture2D(texture, texcoord) * vertexColor;
    if (glint.a < 0.01) {
        discard;
    }

    gl_FragData[0] = glint;
}
