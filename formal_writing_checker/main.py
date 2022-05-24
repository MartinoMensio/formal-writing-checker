import typer

from . import nlp

app = typer.Typer()

@app.command()
def check(text: str):
    """
    Check if the text is formal writing.
    """
    print('checking')
    nlp.check_text(text)