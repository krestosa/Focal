#version 150

uniform sampler2D texture;

in vec2 cloudTexCoord;
in vec4 cloudColor;

layout(location = 0) out vec4 outColor;

void main() {
    vec4 sampled = texture2D(texture, cloudTexCoord) * cloudColor;
    if (sampled.a <= 0.001) {
        discard;
    }
    outColor = sampled;
}
