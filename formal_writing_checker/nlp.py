import spacy
import typer
import logging
from spacy.matcher import Matcher


nlp_instance = None

def get_nlp():
    global nlp_instance
    if not nlp_instance:
        logging.info('loading nlp')
        nlp_instance = spacy.load('en_core_web_lg')
    return nlp_instance

def check_sentences_length(doc, max_length=30):
    logging.info(f'checking sentence length (max_length={max_length})')
    # doc.sents is a generator, don't keep everything in list for memory
    reports = []
    for i, sent in enumerate(doc.sents):
        sent_length = len(sent)
        if sent_length > max_length:
            logging.warning(f'Sentence {i} is too long: {sent.text}')
            reports.append({
                'warning_type': 'sentence_too_long',
                'expectation': max_length,
                'value': sent_length,
                'sentence_index': i,
                'sentence': sent,
                'doc_span_warning': (sent.start + max_length, sent.start + sent_length),
                'explanation': f'length {sent_length} greater than {max_length}.'
            })
    n_sents = i
    
    return {
        'stats': {
            'criterion_name': 'Sentence length',
            'n_sents_total': n_sents,
            'n_sents_warning': len(reports),
        },
        'reports': reports,
    }

def check_passive_voice(doc, nlp):
    logging.info(f'checking sentence passive voice')
    matcher = Matcher(nlp.vocab)
    # first get start and end of the sentences (used later)
    sentences_start_end = []
    for sent in doc.sents:
        sentences_start_end.append((sent.start, sent.end))

    passive_rule = [{'DEP':'nsubjpass'},{'DEP':'aux','OP':'*'},{'DEP':'auxpass'},{'TAG':'VBN'}]
    matcher.add('Passive', [passive_rule])
    matches = matcher(doc)
    reports = []
    for m in matches:
        match_id, start, end = m
        sentence_index = next(i for i, (start_sent, end_sent) in enumerate(sentences_start_end) if start_sent <= start and end_sent >= end)
        reports.append({
                'warning_type': 'sentence_too_long',
                'expectation': 'active voice',
                'value': 'passive voice',
                'sentence_index': sentence_index,
                'sentence': sent,
                'doc_span_warning': (start, end),
                'explanation': f'passive voice'
            })
    return {
        'stats': {
            'criterion_name': 'Sentence Passive Voice',
            'n_sents_total': len(sentences_start_end),
            'n_sents_warning': len(reports),
        },
        'reports': reports,
    }

def write_report(result):
    result_strings = []
    n_sents_total = result['stats']['n_sents_total']
    n_sents_warning = result['stats']['n_sents_warning']
    if n_sents_warning:
        color = typer.colors.RED
    else:
        color = typer.colors.GREEN
    result_strings.extend([
        typer.style(f"CRITERION: {result['stats']['criterion_name']}", fg=typer.colors.CYAN, bold=True),
        ': ',
        typer.style(f"{n_sents_warning} out of {n_sents_total}", fg=color, bold=True),
        ' sentences with warning\n'
    ])
    for report in result['reports']:
        sentence = report['sentence']
        doc_span_warning = report['doc_span_warning']
        doc = sentence.doc
        result_strings.extend([
            f"(sentence #{report['sentence_index']}): ",
            typer.style(report['explanation'], fg=typer.colors.RED, bold=True),
            '\n',
            doc[sentence.start:doc_span_warning[0]].text_with_ws,
            # ' ',
            typer.style(doc[doc_span_warning[0]:doc_span_warning[1]].text_with_ws, fg=typer.colors.RED, bold=False),
            # ' ',
            doc[doc_span_warning[1]:sentence.end].text_with_ws,
            '\n'
        ])

    message = ''.join(result_strings) + '\n\n'
    typer.echo(message)
   

def check_text(text, max_sentence_length=30):
    nlp = get_nlp()
    logging.info('parsing text')
    doc = nlp(text)
    length_results = check_sentences_length(doc, max_sentence_length)
    write_report(length_results)
    passive_results = check_passive_voice(doc, nlp)
    write_report(passive_results)

    logging.info('done')