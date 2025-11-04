# Backend MVP PRD - Générateur de Mémoires (Proof of Concept)

## 🎯 Objectif du MVP

Créer un **proof of concept fonctionnel** qui démontre la capacité à générer automatiquement un mémoire technique Word en réutilisant le contenu d'anciens mémoires.

**Scope** : Backend Python uniquement, interface minimale (ligne de commande ou API simple)

**Durée estimée** : 2-3 semaines

### ⚠️ Contrainte importante découverte

**Deux types de mémoires :**

- **60% en format libre** : On peut utiliser notre propre structure (structure Bernadet standard)
- **40% avec trame imposée** : Template Word fourni par le client dans le RC qu'il faut remplir

**Pour le MVP** : On se concentre sur le **format libre (60%)** uniquement.  
Le support des trames imposées sera ajouté en Phase 2.

### 📋 Structure standard Bernadet (format libre)

Pour les 60% de mémoires en format libre, nous utilisons cette structure :

1. **PRÉSENTATION DE L'ENTREPRISE**
2. **AUTONOMIE MATÉRIELLE ET MAÎTRISE DE L'EXÉCUTION**
3. **ORGANISATION (HUMAINES + PARTENAIRES) GÉNÉRALE DE L'OPÉRATION**
4. **MÉTHODES DE CONSTRUCTION**
   - ⚠️ Inclut dessins manuscrits + coupes types (hors scope MVP)
5. **GESTION DE PROJET ET SUIVI D'EXÉCUTION : PLANNING**
6. **QUALITÉ, SÉCURITÉ ET ENVIRONNEMENT (HSE)**
   - Organisation réserves de réception
   - Organisation réserves de GPA
   - Organisation SAV + délai d'intervention
7. **INSERTION SOCIALE ET ENGAGEMENT RSE**
8. **ANNEXES**

---

## 📦 Stack technique (minimaliste)

| Composant           | Technologie                     | Pourquoi                                      |
| ------------------- | ------------------------------- | --------------------------------------------- |
| **Backend**         | Python 3.11                     | Rapide à développer, excellentes libs         |
| **Framework API**   | FastAPI                         | Simple, rapide, auto-documentation            |
| **Base de données** | Supabase (PostgreSQL)           | Base complète avec APIs, pas de setup serveur |
| **Vector DB**       | Supabase (pgvector)             | Extension intégrée dans Supabase              |
| **Stockage**        | Supabase Storage (S3)           | Stockage intégré, URLs signées                |
| **LLM**             | Claude API (Sonnet 4.5)         | Meilleur pour documents longs                 |
| **Embeddings**      | OpenAI (text-embedding-3-small) | Performant, peu coûteux                       |
| **Parsing PDF**     | pypdf                           | Simple et efficace                            |
| **Parsing Word**    | python-docx                     | Standard pour .docx                           |
| **Génération Word** | python-docx                     | Même lib pour lecture/écriture                |

---

## 🏗️ Architecture simplifiée

```
┌─────────────────────────────────────────────────┐
│              Interface (FastAPI)                 │
│  - Upload mémoires                               │
│  - Upload RC + annexes                           │
│  - Déclencher génération                         │
│  - Télécharger résultat                          │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┴────────────────────────────────┐
│              Services Python                     │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   Parser     │  │     RAG      │            │
│  │  (PDF/Word)  │  │  (pgvector)  │            │
│  └──────────────┘  └──────────────┘            │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   Generator  │  │   Exporter   │            │
│  │  (Claude)    │  │  (python-docx)│           │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
┌──────────┐ ┌──────┐ ┌──────────┐
│ Supabase │ │OpenAI│ │  Claude  │
│          │ │Embed │ │   API    │
│ - Postgre│ │ API  │ └──────────┘
│ - pgvector│└──────┘
│ - Storage│
└──────────┘
```

---

## 📂 Structure du projet

```
memoir-generator/
├── main.py                 # Point d'entrée FastAPI
├── config.py               # Configuration (API keys, Supabase)
├── requirements.txt        # Dépendances
│
├── models/
│   └── schemas.py          # Pydantic schemas
│
├── services/
│   ├── supabase.py         # Client Supabase
│   ├── parser.py           # Parse PDF/DOCX
│   ├── rag.py              # RAG avec pgvector
│   ├── generator.py        # Génération avec Claude
│   └── exporter.py         # Export Word
│
├── utils/
│   └── helpers.py          # Fonctions utilitaires
│
└── templates/
    └── template.docx       # Template Word de base
```

---

## 🗄️ Base de données (Supabase PostgreSQL)

### Schema minimaliste

```sql
-- Extension pgvector pour les embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Table des mémoires référence
CREATE TABLE memoires (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename VARCHAR(255) NOT NULL,
    storage_path VARCHAR(500) NOT NULL,  -- Chemin dans Supabase Storage
    client VARCHAR(255),
    year INTEGER,
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des projets
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    rc_storage_path VARCHAR(500),
    rc_context TEXT,
    status VARCHAR(50) DEFAULT 'draft',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des sections générées
CREATE TABLE sections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    section_type VARCHAR(100) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT,
    order_num INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Table des chunks pour RAG
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    memoire_id UUID NOT NULL REFERENCES memoires(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    embedding vector(1536),  -- OpenAI embeddings dimension
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index pour recherche vectorielle
CREATE INDEX ON document_chunks USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index pour performance
CREATE INDEX idx_chunks_memoire ON document_chunks(memoire_id);
CREATE INDEX idx_sections_project ON sections(project_id, order_num);
```

---

## 🔌 API Endpoints (FastAPI)

### 1. Upload de mémoires référence

```python
POST /memoires/upload
Content-Type: multipart/form-data

Body:
- file: File (PDF ou DOCX)
- client: str (optionnel)
- year: int (optionnel)

Response:
{
    "id": 1,
    "filename": "memoire_toulouse.pdf",
    "status": "uploaded",
    "indexed": false
}
```

### 2. Indexer un mémoire

```python
POST /memoires/{id}/index

Response:
{
    "id": 1,
    "status": "indexed",
    "chunks_created": 45
}
```

### 3. Créer un projet

```python
POST /projects

Body:
{
    "name": "Bande Infra SNCF"
}

Response:
{
    "id": 1,
    "name": "Bande Infra SNCF",
    "status": "draft"
}
```

### 4. Upload RC et annexes

```python
POST /projects/{id}/upload-rc
Content-Type: multipart/form-data

Body:
- file: File (PDF du RC)

Response:
{
    "project_id": 1,
    "rc_uploaded": true
}
```

### 5. Générer le mémoire

```python
POST /projects/{id}/generate

Body:
{
    "memoire_ids": [1, 2],  # IDs des mémoires référence
    "sections": [
        "presentation",
        "organisation",
        "methodologie",
        "moyens_humains",
        "moyens_materiels"
    ]
}

Response:
{
    "project_id": 1,
    "status": "generating",
    "estimated_time": "3 minutes"
}
```

### 6. Télécharger le mémoire

```python
GET /projects/{id}/download

Response: File (DOCX)
```

---

## 🛠️ Implémentation des services

### 1. Parser Service (`services/parser.py`)

```python
from pypdf import PdfReader
from docx import Document
from typing import List, Dict

class ParserService:
    """Parse PDF et DOCX pour extraire le texte."""

    def parse_pdf(self, filepath: str) -> Dict[str, any]:
        """
        Parse un PDF et retourne le texte structuré.
        """
        reader = PdfReader(filepath)
        sections = []

        for page_num, page in enumerate(reader.pages, 1):
            text = page.extract_text()
            sections.append({
                'page': page_num,
                'text': text
            })

        full_text = '\n\n'.join(s['text'] for s in sections)

        return {
            'sections': sections,
            'full_text': full_text,
            'page_count': len(reader.pages)
        }

    def parse_docx(self, filepath: str) -> Dict[str, any]:
        """
        Parse un DOCX et retourne le texte structuré.
        """
        doc = Document(filepath)
        sections = []
        current_section = {'title': 'Introduction', 'content': []}

        for para in doc.paragraphs:
            # Détecter les titres
            if para.style.name.startswith('Heading'):
                if current_section['content']:
                    sections.append(current_section)
                current_section = {
                    'title': para.text,
                    'content': []
                }
            else:
                current_section['content'].append(para.text)

        # Ajouter la dernière section
        if current_section['content']:
            sections.append(current_section)

        full_text = '\n\n'.join(
            f"{s['title']}\n" + '\n'.join(s['content'])
            for s in sections
        )

        return {
            'sections': sections,
            'full_text': full_text,
            'paragraph_count': len(doc.paragraphs)
        }

    def chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """
        Découpe le texte en chunks pour le RAG.
        Simple découpe par caractères avec overlap.
        """
        chunks = []
        overlap = 100

        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            if chunk.strip():
                chunks.append(chunk.strip())

        return chunks
```

---

### 2. RAG Service (`services/rag.py`)

```python
from openai import OpenAI
from typing import List, Dict
from services.supabase import get_supabase

class RAGService:
    """Service de RAG avec Supabase pgvector et OpenAI embeddings."""

    def __init__(self, openai_api_key: str):
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.supabase = get_supabase()

    def generate_embedding(self, text: str) -> List[float]:
        """
        Génère un embedding avec OpenAI.
        """
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def index_memoire(self, memoire_id: str, chunks: List[str], metadata: Dict) -> int:
        """
        Indexe un mémoire dans Supabase avec pgvector.
        """
        chunks_data = []

        for i, chunk in enumerate(chunks):
            # Générer l'embedding
            embedding = self.generate_embedding(chunk)

            chunk_data = {
                'memoire_id': memoire_id,
                'content': chunk,
                'embedding': embedding,
                'metadata': {
                    'chunk_index': i,
                    **metadata
                }
            }
            chunks_data.append(chunk_data)

        # Insertion batch dans Supabase
        result = self.supabase.table('document_chunks').insert(chunks_data).execute()

        return len(chunks_data)

    def search(
        self,
        query: str,
        memoire_ids: List[str] = None,
        n_results: int = 10
    ) -> List[Dict]:
        """
        Recherche les chunks les plus pertinents par similarité vectorielle.
        """
        # Générer l'embedding de la requête
        query_embedding = self.generate_embedding(query)

        # Construire la requête SQL avec pgvector
        # Utilise l'opérateur <=> pour distance cosine
        rpc_params = {
            'query_embedding': query_embedding,
            'match_count': n_results
        }

        if memoire_ids:
            rpc_params['memoire_ids'] = memoire_ids

        # Appel à une fonction PostgreSQL custom (à créer)
        result = self.supabase.rpc('match_documents', rpc_params).execute()

        return result.data
```

**Fonction PostgreSQL à créer dans Supabase :**

```sql
-- Créer cette fonction dans le SQL Editor de Supabase
CREATE OR REPLACE FUNCTION match_documents(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    memoire_ids uuid[] DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        document_chunks.id,
        document_chunks.content,
        document_chunks.metadata,
        1 - (document_chunks.embedding <=> query_embedding) as similarity
    FROM document_chunks
    WHERE
        CASE
            WHEN memoire_ids IS NOT NULL THEN memoire_id = ANY(memoire_ids)
            ELSE true
        END
    ORDER BY document_chunks.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

---

### 3. Generator Service (`services/generator.py`)

```python
from anthropic import Anthropic
from typing import List, Dict

class GeneratorService:
    """Service de génération avec Claude."""

    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def generate_section(
        self,
        section_type: str,
        rc_context: str,
        reference_chunks: List[Dict]
    ) -> str:
        """
        Génère une section de mémoire.
        """
        # Construire le contexte des références
        references_text = "\n\n---\n\n".join(
            f"Extrait de référence {i+1}:\n{chunk['text']}"
            for i, chunk in enumerate(reference_chunks[:5])
        )

        # Construire le prompt
        prompt = self._build_prompt(section_type, rc_context, references_text)

        # Appel à Claude
        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            temperature=0.7,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text

    def _build_prompt(self, section_type: str, rc_context: str, references: str) -> str:
        """
        Construit le prompt pour Claude.
        """
        section_descriptions = {
            'presentation_entreprise': 'Présentation de l\'entreprise (historique, chiffres clés, certifications, implantations)',
            'autonomie_materielle': 'Autonomie matérielle et maîtrise de l\'exécution (équipements, capacités, indépendance)',
            'organisation_generale': 'Organisation générale de l\'opération (organigramme humain, partenaires, coordination)',
            'methodes_construction': 'Méthodes de construction (phasage, techniques, processus de réalisation)',
            'gestion_projet_planning': 'Gestion de projet et suivi d\'exécution avec planning (calendrier, jalons, suivi)',
            'qualite_securite_environnement': 'Qualité, Sécurité et Environnement - HSE (démarche QSE, réserves, SAV)',
            'insertion_sociale_rse': 'Insertion sociale et engagement RSE (heures d\'insertion, actions sociales, environnement)'
        }

        description = section_descriptions.get(section_type, section_type)

        return f"""Tu es un expert en rédaction de mémoires techniques pour le BTP.

**Contexte du projet (extrait du RC) :**
{rc_context}

**Type de section à générer :** {description}

**Contenu de référence (extraits de mémoires similaires) :**
{references}

**Instructions :**
1. Génère une section professionnelle de mémoire technique
2. Réutilise les informations factuelles des références (chiffres, méthodes, équipements)
3. Adapte le contenu au contexte du RC
4. Utilise un ton professionnel mais accessible
5. Privilégie les tableaux aux longues listes
6. Structure : titre H2, sous-titres H3, paragraphes clairs

**Contraintes :**
- Format : Markdown
- Longueur : 500-1000 mots
- Ne pas inventer de données, utiliser uniquement les références

Génère maintenant la section :"""

    def extract_rc_criteria(self, rc_text: str) -> str:
        """
        Extrait les critères clés du RC.
        """
        prompt = f"""Analyse ce Règlement de Consultation et extrait les critères d'évaluation principaux du mémoire technique.

RC :
{rc_text[:3000]}  # Limiter à 3000 chars pour le MVP

Liste uniquement les 5-7 critères les plus importants, de manière concise."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return response.content[0].text
```

---

### 4. Exporter Service (`services/exporter.py`)

```python
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import markdown
from bs4 import BeautifulSoup
from typing import List, Dict

class ExporterService:
    """Service d'export vers Word."""

    def __init__(self, template_path: str = "./templates/template.docx"):
        self.template_path = template_path

    def create_memoire(
        self,
        project_name: str,
        sections: List[Dict]
    ) -> str:
        """
        Crée un document Word complet.

        sections: [
            {
                'title': 'Présentation',
                'content': 'contenu markdown...'
            },
            ...
        ]
        """
        # Charger le template ou créer un nouveau doc
        try:
            doc = Document(self.template_path)
        except:
            doc = Document()
            self._apply_default_styles(doc)

        # Titre du mémoire
        doc.add_heading(f"Mémoire Technique - {project_name}", level=0)
        doc.add_page_break()

        # Ajouter chaque section
        for section in sections:
            self._add_section(doc, section['title'], section['content'])
            doc.add_page_break()

        # Sauvegarder
        output_path = f"./data/output_{project_name.replace(' ', '_')}.docx"
        doc.save(output_path)

        return output_path

    def _add_section(self, doc: Document, title: str, markdown_content: str):
        """
        Ajoute une section au document.
        """
        # Titre de section
        doc.add_heading(title, level=1)

        # Convertir Markdown en HTML
        html = markdown.markdown(markdown_content, extensions=['tables'])
        soup = BeautifulSoup(html, 'html.parser')

        # Parser et ajouter le contenu
        for element in soup.find_all(['h2', 'h3', 'p', 'ul', 'ol', 'table']):
            if element.name == 'h2':
                doc.add_heading(element.text, level=2)
            elif element.name == 'h3':
                doc.add_heading(element.text, level=3)
            elif element.name == 'p':
                doc.add_paragraph(element.text)
            elif element.name in ['ul', 'ol']:
                for li in element.find_all('li'):
                    doc.add_paragraph(li.text, style='List Bullet')
            elif element.name == 'table':
                self._add_table(doc, element)

    def _add_table(self, doc: Document, html_table):
        """
        Ajoute un tableau au document.
        """
        rows = html_table.find_all('tr')
        if not rows:
            return

        # Compter les colonnes
        cols = len(rows[0].find_all(['th', 'td']))

        # Créer le tableau
        table = doc.add_table(rows=len(rows), cols=cols)
        table.style = 'Light Grid Accent 1'

        # Remplir le tableau
        for i, row in enumerate(rows):
            cells = row.find_all(['th', 'td'])
            for j, cell in enumerate(cells):
                table.rows[i].cells[j].text = cell.text.strip()

    def _apply_default_styles(self, doc: Document):
        """
        Applique les styles par défaut (style Bernadet simplifié).
        """
        # Style Heading 1
        h1 = doc.styles['Heading 1']
        h1.font.name = 'Arial'
        h1.font.size = Pt(18)
        h1.font.bold = True
        h1.font.color.rgb = RGBColor(46, 80, 144)  # Bleu

        # Style Heading 2
        h2 = doc.styles['Heading 2']
        h2.font.name = 'Arial'
        h2.font.size = Pt(14)
        h2.font.color.rgb = RGBColor(120, 180, 90)  # Vert

        # Style Normal
        normal = doc.styles['Normal']
        normal.font.name = 'Arial'
        normal.font.size = Pt(11)
```

---

---

### Supabase Service (`services/supabase.py`)

```python
from supabase import create_client, Client
from config import Config

_supabase_client: Client = None

def get_supabase() -> Client:
    """
    Singleton pour le client Supabase.
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )

    return _supabase_client

class SupabaseService:
    """Service pour interagir avec Supabase."""

    def __init__(self):
        self.client = get_supabase()

    # === STORAGE ===

    def upload_file(self, bucket: str, path: str, file_data: bytes) -> str:
        """
        Upload un fichier dans Supabase Storage.
        Retourne le chemin du fichier.
        """
        result = self.client.storage.from_(bucket).upload(
            path=path,
            file=file_data,
            file_options={"content-type": "application/octet-stream"}
        )

        return path

    def get_public_url(self, bucket: str, path: str) -> str:
        """
        Génère une URL publique pour un fichier.
        """
        return self.client.storage.from_(bucket).get_public_url(path)

    def download_file(self, bucket: str, path: str) -> bytes:
        """
        Télécharge un fichier depuis Supabase Storage.
        """
        result = self.client.storage.from_(bucket).download(path)
        return result

    # === DATABASE ===

    def create_memoire(self, filename: str, storage_path: str, client: str = None, year: int = None) -> str:
        """
        Crée un enregistrement de mémoire.
        Retourne l'UUID.
        """
        data = {
            'filename': filename,
            'storage_path': storage_path,
            'client': client,
            'year': year
        }

        result = self.client.table('memoires').insert(data).execute()
        return result.data[0]['id']

    def get_memoire(self, memoire_id: str) -> dict:
        """
        Récupère un mémoire par son ID.
        """
        result = self.client.table('memoires').select('*').eq('id', memoire_id).execute()
        return result.data[0] if result.data else None

    def mark_memoire_indexed(self, memoire_id: str):
        """
        Marque un mémoire comme indexé.
        """
        self.client.table('memoires').update({'indexed': True}).eq('id', memoire_id).execute()

    def list_memoires(self) -> list:
        """
        Liste tous les mémoires.
        """
        result = self.client.table('memoires').select('*').order('created_at', desc=True).execute()
        return result.data

    def create_project(self, name: str) -> str:
        """
        Crée un nouveau projet.
        Retourne l'UUID.
        """
        data = {'name': name}
        result = self.client.table('projects').insert(data).execute()
        return result.data[0]['id']

    def get_project(self, project_id: str) -> dict:
        """
        Récupère un projet par son ID.
        """
        result = self.client.table('projects').select('*').eq('id', project_id).execute()
        return result.data[0] if result.data else None

    def update_project_rc(self, project_id: str, rc_storage_path: str, rc_context: str):
        """
        Met à jour le RC d'un projet.
        """
        data = {
            'rc_storage_path': rc_storage_path,
            'rc_context': rc_context
        }
        self.client.table('projects').update(data).eq('id', project_id).execute()

    def update_project_status(self, project_id: str, status: str):
        """
        Met à jour le statut d'un projet.
        """
        self.client.table('projects').update({'status': status}).eq('id', project_id).execute()

    def list_projects(self) -> list:
        """
        Liste tous les projets.
        """
        result = self.client.table('projects').select('*').order('created_at', desc=True).execute()
        return result.data

    def create_section(self, project_id: str, section_type: str, title: str, content: str, order_num: int) -> str:
        """
        Crée une section générée.
        Retourne l'UUID.
        """
        data = {
            'project_id': project_id,
            'section_type': section_type,
            'title': title,
            'content': content,
            'order_num': order_num
        }
        result = self.client.table('sections').insert(data).execute()
        return result.data[0]['id']

    def get_sections(self, project_id: str) -> list:
        """
        Récupère toutes les sections d'un projet.
        """
        result = self.client.table('sections').select('*').eq('project_id', project_id).order('order_num').execute()
        return result.data
```

---

## 🚀 API Routes (FastAPI)

### `main.py`

```python
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from typing import List
import tempfile
import os

from services.parser import ParserService
from services.rag import RAGService
from services.generator import GeneratorService
from services.exporter import ExporterService
from services.supabase import SupabaseService
from config import Config

app = FastAPI(title="Memoir Generator MVP")

# Services
parser = ParserService()
rag = RAGService(openai_api_key=Config.OPENAI_API_KEY)
generator = GeneratorService(api_key=Config.CLAUDE_API_KEY)
exporter = ExporterService()
supabase = SupabaseService()

# === MÉMOIRES RÉFÉRENCE ===

@app.post("/memoires/upload")
async def upload_memoire(
    file: UploadFile = File(...),
    client: str = None,
    year: int = None
):
    """Upload un mémoire de référence."""

    # Vérifier l'extension
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(400, "Format non supporté. PDF ou DOCX uniquement.")

    # Lire le fichier
    file_data = await file.read()

    # Upload vers Supabase Storage
    storage_path = f"memoires/{file.filename}"
    supabase.upload_file('documents', storage_path, file_data)

    # Créer l'enregistrement en base
    memoire_id = supabase.create_memoire(file.filename, storage_path, client, year)

    return {
        "id": memoire_id,
        "filename": file.filename,
        "status": "uploaded",
        "indexed": False
    }

@app.post("/memoires/{memoire_id}/index")
async def index_memoire(memoire_id: str):
    """Indexe un mémoire pour le RAG."""

    memoire = supabase.get_memoire(memoire_id)
    if not memoire:
        raise HTTPException(404, "Mémoire non trouvé")

    # Télécharger le fichier depuis Supabase Storage
    file_data = supabase.download_file('documents', memoire['storage_path'])

    # Sauvegarder temporairement
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(memoire['filename'])[1]) as tmp:
        tmp.write(file_data)
        tmp_path = tmp.name

    try:
        # Parser le fichier
        if memoire['filename'].endswith('.pdf'):
            parsed = parser.parse_pdf(tmp_path)
        else:
            parsed = parser.parse_docx(tmp_path)

        # Chunker le texte
        chunks = parser.chunk_text(parsed['full_text'])

        # Indexer dans pgvector
        metadata = {
            'filename': memoire['filename'],
            'client': memoire['client'],
            'year': memoire['year']
        }
        chunks_count = rag.index_memoire(memoire_id, chunks, metadata)

        # Mettre à jour la base
        supabase.mark_memoire_indexed(memoire_id)

        return {
            "id": memoire_id,
            "status": "indexed",
            "chunks_created": chunks_count
        }
    finally:
        # Nettoyer le fichier temporaire
        os.unlink(tmp_path)

@app.get("/memoires")
async def list_memoires():
    """Liste tous les mémoires."""
    return supabase.list_memoires()

# === PROJETS ===

@app.post("/projects")
async def create_project(name: str):
    """Crée un nouveau projet."""
    project_id = supabase.create_project(name)
    return {
        "id": project_id,
        "name": name,
        "status": "draft"
    }

@app.post("/projects/{project_id}/upload-rc")
async def upload_rc(project_id: str, file: UploadFile = File(...)):
    """Upload le RC du projet."""

    project = supabase.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projet non trouvé")

    # Lire le fichier
    file_data = await file.read()

    # Upload vers Supabase Storage
    storage_path = f"projects/{project_id}/rc.pdf"
    supabase.upload_file('documents', storage_path, file_data)

    # Sauvegarder temporairement pour parser
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        tmp.write(file_data)
        tmp_path = tmp.name

    try:
        # Parser pour extraire contexte
        parsed = parser.parse_pdf(tmp_path)
        rc_context = parsed['full_text'][:2000]  # Premiers 2000 chars

        # Mettre à jour le projet
        supabase.update_project_rc(project_id, storage_path, rc_context)

        return {
            "project_id": project_id,
            "rc_uploaded": True
        }
    finally:
        os.unlink(tmp_path)

@app.post("/projects/{project_id}/generate")
async def generate_memoire(
    project_id: str,
    memoire_ids: List[str],
    sections: List[str]
):
    """Génère le mémoire technique."""

    project = supabase.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projet non trouvé")

    if not project['rc_storage_path']:
        raise HTTPException(400, "RC non uploadé")

    # RC context
    rc_context = project['rc_context'] or "Projet de construction"

    # Générer chaque section
    generated_sections = []

    for i, section_type in enumerate(sections, 1):
        # Recherche RAG
        query = f"{section_type} organisation chantier méthodologie"
        chunks = rag.search(query, memoire_ids, n_results=10)

        # Génération
        content = generator.generate_section(
            section_type=section_type,
            rc_context=rc_context,
            reference_chunks=chunks
        )

        # Sauvegarder en base
        section_id = supabase.create_section(
            project_id=project_id,
            section_type=section_type,
            title=section_type.replace('_', ' ').title(),
            content=content,
            order_num=i
        )

        generated_sections.append({
            'id': section_id,
            'type': section_type,
            'title': section_type.replace('_', ' ').title()
        })

    # Marquer le projet comme prêt
    supabase.update_project_status(project_id, 'ready')

    return {
        "project_id": project_id,
        "status": "ready",
        "sections": generated_sections
    }

@app.get("/projects/{project_id}/download")
async def download_memoire(project_id: str):
    """Télécharge le mémoire généré."""

    project = supabase.get_project(project_id)
    if not project:
        raise HTTPException(404, "Projet non trouvé")

    # Récupérer les sections
    sections = supabase.get_sections(project_id)

    if not sections:
        raise HTTPException(400, "Aucune section générée")

    # Créer le document Word
    output_path = exporter.create_memoire(
        project_name=project['name'],
        sections=sections
    )

    return FileResponse(
        output_path,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        filename=f"memoire_{project['name'].replace(' ', '_')}.docx"
    )

@app.get("/projects")
async def list_projects():
    """Liste tous les projets."""
    return supabase.list_projects()

# === HEALTH CHECK ===

@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

---

## ⚙️ Configuration (`config.py`)

```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

    # Supabase
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')

    # Template
    TEMPLATE_PATH = './templates/template.docx'
```

---

## 📦 Requirements (`requirements.txt`)

```txt
# Web framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Supabase
supabase==2.3.0

# Document processing
pypdf==3.17.1
python-docx==1.1.0
beautifulsoup4==4.12.2
markdown==3.5.1

# LLM & Embeddings
anthropic==0.7.8
openai==1.6.1

# Utils
python-dotenv==1.0.0
```

---

## 🚀 Installation et lancement

### 1. Setup Supabase

```bash
# 1. Créer un compte sur supabase.com
# 2. Créer un nouveau projet
# 3. Dans le SQL Editor, exécuter le script de création des tables (voir section Database)
# 4. Activer pgvector : Extensions → rechercher "vector" → Enable
# 5. Créer un bucket "documents" dans Storage
# 6. Copier l'URL et la clé API du projet
```

### 2. Installation locale

```bash
# Créer l'environnement virtuel
python -m venv venv
source venv/bin/activate  # ou venv\Scripts\activate sur Windows

# Installer les dépendances
pip install -r requirements.txt

# Créer le dossier templates
mkdir -p templates
```

### 3. Configuration

```bash
# Créer le fichier .env
cat > .env << EOF
CLAUDE_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-openai-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key-here
EOF
```

### 4. Lancer le serveur

```bash
uvicorn main:app --reload --port 8000
```

L'API sera accessible sur `http://localhost:8000`

Documentation auto-générée : `http://localhost:8000/docs`

---

## 📝 Workflow d'utilisation (MVP)

### Étape 1 : Uploader des mémoires référence

```bash
curl -X POST "http://localhost:8000/memoires/upload" \
  -F "file=@memoire_toulouse.pdf" \
  -F "client=Toulouse Metropole" \
  -F "year=2024"

# Réponse :
# {"id": 1, "filename": "memoire_toulouse.pdf", "status": "uploaded", "indexed": false}
```

### Étape 2 : Indexer les mémoires

```bash
curl -X POST "http://localhost:8000/memoires/1/index"

# Réponse :
# {"id": 1, "status": "indexed", "chunks_created": 45}
```

### Étape 3 : Créer un projet

```bash
curl -X POST "http://localhost:8000/projects?name=Bande%20Infra%20SNCF"

# Réponse :
# {"id": 1, "name": "Bande Infra SNCF", "status": "draft"}
```

### Étape 4 : Uploader le RC

```bash
curl -X POST "http://localhost:8000/projects/1/upload-rc" \
  -F "file=@rc_sncf.pdf"

# Réponse :
# {"project_id": 1, "rc_uploaded": true}
```

### Étape 5 : Générer le mémoire

```bash
curl -X POST "http://localhost:8000/projects/1/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "memoire_ids": [1, 2],
    "sections": [
      "presentation",
      "organisation",
      "methodologie",
      "moyens_humains",
      "moyens_materiels"
    ]
  }'

# Réponse :
# {
#   "project_id": 1,
#   "status": "ready",
#   "sections": [...]
# }
```

### Étape 6 : Télécharger le résultat

```bash
curl -X GET "http://localhost:8000/projects/1/download" \
  --output memoire.docx
```

---

## 🎯 Périmètre MVP

### ✅ Ce qui est inclus

- Upload de mémoires référence (PDF/DOCX)
- Parsing et chunking automatique
- Indexation avec RAG (ChromaDB)
- Upload du RC
- Génération de 5 sections de base
- Export Word avec style minimal
- API REST complète
- Base de données SQLite

### ❌ Ce qui n'est PAS inclus (pour plus tard)

- Interface web (frontend)
- Authentification utilisateur
- Upload d'images/annexes
- Régénération de sections
- Versioning
- Templates Word personnalisables
- Multi-utilisateurs
- Monitoring/logs
- Tests automatisés
- Déploiement production

---

## 📊 Estimation de charge

### Développement

| Tâche                      | Temps estimé  |
| -------------------------- | ------------- |
| Setup projet + structure   | 0.5 jour      |
| Parser service             | 1 jour        |
| RAG service (ChromaDB)     | 1 jour        |
| Generator service (Claude) | 1 jour        |
| Exporter service (Word)    | 1 jour        |
| API routes (FastAPI)       | 1 jour        |
| Database layer             | 0.5 jour      |
| Tests manuels              | 1 jour        |
| Documentation              | 0.5 jour      |
| **Total**                  | **7-8 jours** |

### Coûts

| Poste                          | Coût        |
| ------------------------------ | ----------- |
| Développement (1 dev, 8 jours) | ~4 000€     |
| Supabase (Free tier)           | 0€          |
| Claude API (tests)             | ~20€        |
| OpenAI Embeddings (tests)      | ~5€         |
| **Total MVP**                  | **~4 025€** |

**Note** : Supabase Free tier inclut :

- 500 MB de stockage
- 2 GB de bande passante
- 50 000 utilisateurs actifs mensuels
- Largement suffisant pour un MVP

---

## 🧪 Tests du MVP

### Test complet

```python
# test_mvp.py
import requests
import os

BASE_URL = "http://localhost:8000"

# 1. Upload mémoire
with open("test_data/memoire1.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/memoires/upload",
        files={"file": f},
        data={"client": "Test Client", "year": 2024}
    )
    memoire_id = response.json()["id"]
    print(f"✓ Mémoire uploadé: {memoire_id}")

# 2. Indexer
response = requests.post(f"{BASE_URL}/memoires/{memoire_id}/index")
print(f"✓ Mémoire indexé: {response.json()['chunks_created']} chunks")

# 3. Créer projet
response = requests.post(
    f"{BASE_URL}/projects",
    params={"name": "Test Project"}
)
project_id = response.json()["id"]
print(f"✓ Projet créé: {project_id}")

# 4. Upload RC
with open("test_data/rc.pdf", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/projects/{project_id}/upload-rc",
        files={"file": f}
    )
    print(f"✓ RC uploadé")

# 5. Générer
response = requests.post(
    f"{BASE_URL}/projects/{project_id}/generate",
    json={
        "memoire_ids": [memoire_id],
        "sections": ["presentation", "methodologie"]
    }
)
print(f"✓ Mémoire généré: {len(response.json()['sections'])} sections")

# 6. Télécharger
response = requests.get(f"{BASE_URL}/projects/{project_id}/download")
with open("output_test.docx", "wb") as f:
    f.write(response.content)
print(f"✓ Mémoire téléchargé: output_test.docx")
```

---

## 🔄 Prochaines étapes (après MVP)

1. **Support des trames imposées (40% des mémoires)**
   - Parser les templates Word fournis dans le RC
   - Identifier les zones à remplir (form fields, tableaux, etc.)
   - Remplir automatiquement ces zones avec le contenu généré
2. **Interface web simple** (Streamlit ou Gradio)

3. **Amélioration du chunking** (préservation de structure)

4. **Templates Word** professionnels (style Bernadet avec charte graphique)

5. **Régénération de sections**

6. **Upload d'images/annexes**

7. **Génération d'organigrammes** (qui changent par projet !)

8. **Interface d'édition**

9. **Multi-utilisateurs**

10. **Déploiement cloud**

### 💡 Potentiel commercial

> "Tous les lots (électricien, plaquiste, plombier, etc) sont soumis à cet exercice imposé. [...] il y a du potentiel..."

**Opportunité identifiée :** Ce besoin existe pour **tous les corps de métier du BTP**. Potentiel de commercialisation important si le produit fonctionne bien.

---

## 📚 Documentation API

La documentation interactive est disponible automatiquement via FastAPI :

- **Swagger UI** : http://localhost:8000/docs
- **ReDoc** : http://localhost:8000/redoc

---

## ✅ Critères de succès du MVP

Le MVP sera considéré comme réussi si :

1. ✅ On peut uploader et indexer des mémoires PDF/DOCX
2. ✅ On peut créer un projet et uploader un RC
3. ✅ La génération produit des sections cohérentes
4. ✅ Le document Word exporté est lisible et structuré
5. ✅ Le temps de génération est < 5 minutes
6. ✅ Le contenu réutilise les références pertinentes

---

**Ce MVP peut être développé en 7-8 jours et permettra de valider l'approche technique avant d'investir dans une solution complète.**
