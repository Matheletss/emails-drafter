"""
Email template engine — fixed template with only two substitutions.

No AI rewriting. No paraphrasing. Only {{PERSON_NAME}} and {{COMPANY_NAME}}.
"""

_BODY_TEMPLATE_HTML = """<div style="font-family: Arial, sans-serif; font-size: 14px; color: #222;">
<p>Hello {{PERSON_NAME}},</p>

<p>I hope you are doing well.</p>

<p>I am writing this email for an internship at {{COMPANY_NAME}} for machine learning engineering or an Artificial Intelligence role.</p>

<p>I am Sagar, a final-year engineering student from Birla Institute of Technology pursuing Mathematics and Computing.</p>

<p>I dont want to waste you time. So here is something about my work.</p>

<ol style="padding-left: 24px; line-height: 1.8;">
<li style="margin-bottom: 12px;">At The Linux Foundation, I worked on ML applications for telecom infrastructure and data anonymization, including autoencoder-based pipelines while evaluating privacy preservation and model performance</li>

<li style="margin-bottom: 12px;">I co-founded Emplo AI, where I architected the product end-to-end across frontend, backend, database, and AI/ML, processing 2,000+ resumes and conducting 100+ AI interviews.</li>

<li style="margin-bottom: 12px;">At Modal AI, I worked on multimodal video understanding using LaViLa and VideoRecap, processing 1,000+ video clips and reducing inference latency by ~50%.</li>

<li style="margin-bottom: 12px;">Built DataWire, a multi-agent AI analytics platform using LangGraph and RAG, with specialized agents, real-time streaming, Redis caching, and external data integration.</li>

<li style="margin-bottom: 12px;">Currently building Sponsa, a UPI-based tipping platform for YouTube Live streamers, working across React, FastAPI, MongoDB, Cashfree, WebSockets, and OBS.</li>

<li style="margin-bottom: 12px;">I am familiar with PyTorch, TensorFlow/Keras, Scikit-Learn, NLP, RAG, LLMs, LangGraph, and building AI systems end-to-end.</li>

<li style="margin-bottom: 12px;">I have published research on multi-objective optimization using NSGA-II, with the work provisionally accepted as a book chapter in <i>Decision Analytics for Tourism Planning and Management</i>.</li>
</ol>

<p>I don't care about working hours and all, I just want to learn as much as possible and contribute to the team at {{COMPANY_NAME}}.</p>

<p>Here is resume:<br>
<a href="https://drive.google.com/file/d/1Fs4htOssxanFrnsIUI6RSWCR633EhgkD/view?usp=sharing">https://drive.google.com/file/d/1Fs4htOssxanFrnsIUI6RSWCR633EhgkD/view?usp=sharing</a></p>

<p>Thanks &amp; Regards<br>
Sagar</p>
</div>"""

# Plain text version for preview in the dashboard
_BODY_TEMPLATE_PLAIN = """Hello {{PERSON_NAME}},

I hope you are doing well.

I am writing this email for an internship at {{COMPANY_NAME}} for machine learning engineering or an Artificial Intelligence role.

I am Sagar, a final-year engineering student from Birla Institute of Technology pursuing Mathematics and Computing.

I dont want to waste you time. So here is something about my work.

    1. At The Linux Foundation, I worked on ML applications for telecom infrastructure and data anonymization, including autoencoder-based pipelines while evaluating privacy preservation and model performance

    2. I co-founded Emplo AI, where I architected the product end-to-end across frontend, backend, database, and AI/ML, processing 2,000+ resumes and conducting 100+ AI interviews.

    3. At Modal AI, I worked on multimodal video understanding using LaViLa and VideoRecap, processing 1,000+ video clips and reducing inference latency by ~50%.

    4. Built DataWire, a multi-agent AI analytics platform using LangGraph and RAG, with specialized agents, real-time streaming, Redis caching, and external data integration.

    5. Currently building Sponsa, a UPI-based tipping platform for YouTube Live streamers, working across React, FastAPI, MongoDB, Cashfree, WebSockets, and OBS.

    6. I am familiar with PyTorch, TensorFlow/Keras, Scikit-Learn, NLP, RAG, LLMs, LangGraph, and building AI systems end-to-end.

    7. I have published research on multi-objective optimization using NSGA-II, with the work provisionally accepted as a book chapter in Decision Analytics for Tourism Planning and Management.

I don't care about working hours and all, I just want to learn as much as possible and contribute to the team at {{COMPANY_NAME}}.

Here is resume:

https://drive.google.com/file/d/1Fs4htOssxanFrnsIUI6RSWCR633EhgkD/view?usp=sharing

Thanks & Regards
Sagar"""

_SUBJECT_TEMPLATE = "Would love to work at @{{COMPANY_NAME}}"


def generate_subject(company_name: str) -> str:
    """Return the personalised subject line."""
    return _SUBJECT_TEMPLATE.replace("{{COMPANY_NAME}}", company_name)


def generate_body(person_name: str, company_name: str) -> str:
    """Return the personalised email body (HTML for Gmail)."""
    return (
        _BODY_TEMPLATE_HTML
        .replace("{{PERSON_NAME}}", person_name)
        .replace("{{COMPANY_NAME}}", company_name)
    )


def generate_body_plain(person_name: str, company_name: str) -> str:
    """Return the personalised email body (plain text for preview)."""
    return (
        _BODY_TEMPLATE_PLAIN
        .replace("{{PERSON_NAME}}", person_name)
        .replace("{{COMPANY_NAME}}", company_name)
    )
