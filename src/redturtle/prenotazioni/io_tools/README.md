# IO tools

[![pypi](https://img.shields.io/pypi/v/io_tools.svg)](https://pypi.python.org/pypi/io_tools)


## IO

API Python ad alto livello per i servizi di messaggistica App IO 

* Free software: GNU General Public License v3

## Quickstart

Utilizzo in ambiente di sviluppo:

```bash
    % github clone https://github.com/mamico/python-io-tools
    % cd io_tools
    % virtualenv .
    % . bin/activate
    % python setup.py develop
```

Con zc.buildout:

```ini
    [buildout]
    extensions = mr.developer
    parts = io

    [io]
    recipe = zc.recipe.egg
    eggs = io_tools

    [sources]
    io_tools = git https://github.com/mamico/python-io-tools.git
```

Installazione da pypi (TODO):

```bash
    % pip install io_tools
```

## CLI

    TODO

```bash
    % io_tools --config example_config.yml --message example_msg.yml
```

## API

```python

    >>> from datetime import datetime
    >>> from io_tools.api import Api
    >>> api = Api(secret='api-secret-from-developer.io.italia.it')
```

Per evitare multipli invii dello stesso messaggio è possibile utilizzare un
identificativo unico per la propria applicazione del messaggio (key). Da non confondere 
con il msgid rilasciato da IO.

```python
    >>> key = 'my-first-message'
    >>> fiscal_code = 'AAAAAA00A00A000A'
    >>> subject = 'Titolo di prova'
```

Il corpo del messaggio può essere formattato in [Markdown](https://markdown-guide.readthedocs.io/). Al momento sono consentite solo alcune formattazioni: intestazioni, grassetto, italico, elenco puntato, numerato. [Allowed Markdown formatting](https://developer.io.italia.it/openapi.html#section/Messages/Allowed-Markdown-formatting).

```python    
    >>> body = '''# Lorem Ipsum
    ... ## intestazione2
    ... Testo del messaggio in *markdown*
    ... * lista
    ... * lista
    ... '''
```

Il messaggio può contenere eventualmente informazioni circa un avviso di pagamento, l'ammontare
della cifra (campo amount) è indicata in centesimi di euro, il numero di avviso di pagamento (notice_number)
segue le specifiche indicate nella sezione 2.2 del documento [Specifiche attuative dei codici identificativi di versamento,riversamento e rendicontazione](https://docs.italia.it/italia/pagopa/pagopa-codici-docs/it/stabile/_docs/Capitolo2.html#numero-avviso-e-codice-iuv-nel-caso-di-pagamenti-attivati-presso-i-psp).
```
    <aux digit (1n)>[<application code> (2n)]<codice IUV (15|17n)>
```

La lunghezza del numero di avviso di pagamento deve essere di 18 cifre, in una delle forme:

* '0' + 2 cifre per `application_code` + 13 codice IUV Base + 2 cifre check digit. [Valore 0 del componente Aux Digit](https://docs.italia.it/italia/pagopa/pagopa-codici-docs/it/stabile/_docs/Capitolo2.html#valore-0-del-componente-aux-digit)
* '1' + 17 cifre codice IUV senza check digit. [Valore 1 del componente Aux Digit](https://docs.italia.it/italia/pagopa/pagopa-codici-docs/it/stabile/_docs/Capitolo2.html#valore-1-del-componente-aux-digit) 
* '2' + 15 cifre codice IUV + 2 cifre check digit. [Valore 2 del componente Aux Digit](https://docs.italia.it/italia/pagopa/pagopa-codici-docs/it/stabile/_docs/Capitolo2.html#valore-2-del-componente-aux-digit) 
* '3' + 2 cifre codice di segregazione + 13 cifre codice IUV + 2 cifre check digit. [Valore 3 del componente Aux Digit](https://docs.italia.it/italia/pagopa/pagopa-codici-docs/it/stabile/_docs/Capitolo2.html#valore-3-del-componente-aux-digit) 


```python    

    >>> payment_data = {
    ...     'amount': 10,
    ...     'notice_number': '012345678901234567',
    ...     'invalid_after_due_date': False,
    ... }
```

```python

    >>> msgid = api.send_message(
    ...     fiscal_code=fiscal_code,
    ...     subject=subject,
    ...     body=body,
    ...     payment_data=payment_data,
    ...     due_date=datetime(2021, 3, 14, 12, 0, 0),
    ...     key=key,
    ... )

```

### Storage

E' possibile definire uno storage per tenere traccia degli invii effettuati, malfunzionameti e evitare
doppi invii dello stesso messaggio.

Lo storage deve derviare dalla classe io.tools.storage.Storage e implementare i tre metodi:

* `def get_message(self, key):`
* `def create_message(self, key, fiscal_code, subject, body, payment_data, due_date):`
* `def update_message(self, key, **kwargs):`

In `io.tools.rdbms.Storage` è implementato uno storage su DB relazionale che usa una tabella Message per
la persistenza, i parametri per la connessione al db seguono la sintassi dell'ORM Pony
https://docs.ponyorm.org/database.html#binding-the-database-object-to-a-specific-database

Esempio SQLite:

```python:

    >>> from io.tools.rdbms import Storage 
    >>> storage = Storage(dict(
    ...     provider='sqlite', 
    ...     filename='/path/to/database.sqlite', 
    ...     create_db=True,
    ...     create_tables=True,
    ... ))
```

Esempio PostgreSQL:

```bash
    % pip install py psycopg2
```

```python
    >>> storage = Storage(dict(
    ...     provider='postgres', 
    ...     host='localhost', 
    ...     port='5432'
    ...     user='notice', 
    ...     password='Notice',
    ...     database='notice_db', 
    ...     create_tables=True,
    ... ))
```

```python
    >>> api = Api(secret='api-secret-from-developer.io.italia.it', storage=storage)
```

## Features

* TODO

## TODO

## Credits

