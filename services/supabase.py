from supabase import create_client, Client
from config import Config

_supabase_client: Client = None

def get_supabase() -> Client:
    """
    Singleton for the client Supabase.
    """
    global _supabase_client

    if _supabase_client is None:
        _supabase_client = create_client(
            Config.SUPABASE_URL,
            Config.SUPABASE_KEY
        )

    return _supabase_client

class SupabaseService:
    """Service for interacting with Supabase."""

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
