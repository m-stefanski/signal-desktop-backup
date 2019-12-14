from os.path import expanduser, join, isdir, exists
from os import mkdir, getcwd
import json
import sys
from pysqlcipher3 import dbapi2 as sqlite
import hashlib
import re
import json
import time

def get_encryption_key(config_path):
    try:
        print(f"Opening config from {CONFIG_FILE}")
        with open(config_path) as f:
            config = json.load(f)
            key = config["key"]
            print(f"Found key starting with: {key[0:4]}...")
            return key
    except FileNotFoundError:
        print("Config file not found!")
        sys.exit(1)
    except KeyError:
        print("Config file does not contain key!")
        sys.exit(1)  

def get_connection(database, key):
    try:
        print(f"Opening database from {database}")
        conn = sqlite.connect(database)
        conn.execute(f"PRAGMA key = \"x'{key}'\"")
        conn.execute("SELECT * FROM sqlite_master").fetchall()
        return conn
    except sqlite.OperationalError as e:
        print(f"OperationalError: {e}")
        sys.exit(1)
    except sqlite.DatabaseError as e:
        try:
            print(f"Opening database from {database} (using sqlcipher 3)")
            conn = sqlite.connect(database)
            conn.execute(f"PRAGMA key = \"x'{key}'\"")
            conn.execute("PRAGMA cipher_compatibility = 3")
            conn.execute("SELECT * FROM sqlite_master").fetchall()
            return conn
        except:
            print(f"DatabaseError: {e}")
            sys.exit(1)

def prepare_export_structure():
    import time
    TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
    
    BACKUP_DIR = join(getcwd(), f"signal_backup_{TIMESTAMP}")
    mkdir(BACKUP_DIR)

    CONVERSATIONS_DIR = join(BACKUP_DIR, 'conversations')
    mkdir(CONVERSATIONS_DIR)

    return BACKUP_DIR, CONVERSATIONS_DIR

def get_conversation_filename(id, name):

    def get_valid_filename(s):
        s = str(s).strip().replace(' ', '_')
        return re.sub(r'(?u)[^-\w.]', '', s)

    hash = hashlib.md5(name.encode('utf-8')).hexdigest()
    return f"{get_valid_filename(name)}_{hash}.html"

def create_css(conversations_dir):
    CSS_FILENAME = join(conversations_dir, 'style.css')

    with open(CSS_FILENAME, 'w') as css_file:
        css_file.write("""
.speech-bubble {
	position: relative;
	border-radius: .4em;
}
.incoming {
    background: #aaaaaa;
}
.outgoing {
    background: #dddddd;
}
""")


def create_html_index(conversations, backup_dir):
    INDEX_FILENAME = join(backup_dir, 'conversations.html')

    with open(INDEX_FILENAME, 'w') as html_file:
        html_file.write("<html><head><meta charset=\"utf-8\"/></head><body><h1>Conversations</h1><ul>") 
        for (id, name) in conversations:
            conversation_filename=get_conversation_filename(id, name)
            html_file.write(f"<li><a href=\"conversations/{conversation_filename}\">{name}</a></li>")
        html_file.write("</ul></body></html>") 
        html_file.close()


def parse_message_row(row_json):
    row = json.loads(row_json)

    if row.get("type") in ['incoming', 'outgoing']:
        mess_type = row.get("type")
    else:
        return None

    attachments = ''
    if "attachments" in row:
        for att in row.get("attachments"):
            attachments += "<br/>"
            if att.get("fileName") is not None:
                attachments += att.get("fileName")
            else:
                attachments += "[Filename unknown]"

    received = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row["received_at"]/1000))
    body = row.get("body")

    return f"<div class=\"speech-bubble {mess_type}\">{received}: {body}{attachments}</div>"


def create_conversation_pages(conversations, conversation_dir):
    for (id, name) in conversations:
        print(f"Backing up '{name}'...")

        CONVERSATION_FILENAME = join(conversation_dir, get_conversation_filename(id, name))
        
        try:
            messages = conn.execute(f"SELECT json FROM messages where conversationId=\"{id}\" order by sent_at asc").fetchall()

            with open(CONVERSATION_FILENAME, 'w') as html_file:
                html_file.write(f"<html><head><meta charset=\"utf-8\"/><link rel=\"stylesheet\" type=\"text/css\" href=\"style.css\"></head><body><h1>Conversation with {name}</h1>") 
                
                for (json) in messages:
                    html_row = parse_message_row(json[0])
                    if html_row is not None:
                        html_file.write(html_row)

                html_file.write("</body></html>") 
                html_file.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print(f'Starting Signal Desktop backup...')

    if sys.platform == "darwin":
        HOME_DIR = expanduser("~")
        SIGNAL_DIR = join(HOME_DIR, 'Library', 'Application Support', 'Signal')
        CONFIG_FILE = join(SIGNAL_DIR, "config.json")
        DATABASE_FILE = join(SIGNAL_DIR, "sql", "db.sqlite")
    else:
        print("Only MacOS tested so far, extiting.")
        sys.exit(0)

    key = get_encryption_key(CONFIG_FILE)
    conn = get_connection(DATABASE_FILE, key)

    BACKUP_DIR, CONVERSATIONS_DIR = prepare_export_structure()

    conversations = conn.execute("SELECT id, name FROM conversations").fetchall()

    create_html_index(conversations, BACKUP_DIR)
    create_css(CONVERSATIONS_DIR)
    create_conversation_pages(conversations, CONVERSATIONS_DIR)

    

