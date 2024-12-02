<!-- ID: 878ae1db-766f-49c7-a1a8-59f7be1fee8f -->
{% if context.release_preview -%}
### Release Notes
<details>
<summary>Just wanted to say</summary>

![success](https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExMTlmYjI2N2M0Yjk3YzQwOGZjOTYzYWRlNjQwNjkwNWJiZmI2MzhjMyZlcD12MV9pbnRlcm5hbF9naWZzX2dpZklkJmN0PWc/1Z02vuppxP1Pa/giphy.gif)

</details>

{{context.release_preview.changelog}}
{% else %}
![error](https://media.giphy.com/media/mq5y2jHRCAqMo/giphy.gif)

### You are missing a RELEASE.md or it is not formatted correctly.

**{{context.release_preview.error}}**
Here is an example format:
```md
Release type: <patch/minor/major>
[//]: # (describe your changes here...)
```
{% endif %}
