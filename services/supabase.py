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
        # Determine content type based on file extension
        content_type = "application/octet-stream"
        if path.lower().endswith('.pdf'):
            content_type = "application/pdf"
        elif path.lower().endswith(('.docx', '.doc')):
            content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

        try:
            result = self.client.storage.from_(bucket).upload(
                path=path,
                file=file_data,
                file_options={
                    "content-type": content_type,
                    "upsert": "true"  # Allow overwriting if file exists
                }
            )
            return path
        except Exception as e:
            print(f"❌ Supabase Storage upload error: {type(e).__name__}: {str(e)}")
            raise

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

    def delete_memoire(self, memoire_id: str) -> bool:
        """
        Supprime un mémoire et ses fichiers associés.

        Grâce à ON DELETE CASCADE dans le schema, cela supprimera automatiquement:
        - Les chunks dans document_chunks
        - Les embeddings/vectors associés

        Args:
            memoire_id: UUID du mémoire à supprimer

        Returns:
            True si la suppression a réussi
        """
        # Get memoire to get storage path
        memoire = self.get_memoire(memoire_id)
        if not memoire:
            return False

        # Delete file from storage
        try:
            storage_path = memoire['storage_path']
            self.client.storage.from_('memoires').remove([storage_path])
            print(f"✅ Deleted file from storage: {storage_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not delete file from storage: {e}")
            # Continue anyway to delete database record

        # Delete database record (CASCADE will delete related chunks/embeddings)
        self.client.table('memoires').delete().eq('id', memoire_id).execute()
        print(f"✅ Deleted memoire record and related data: {memoire_id}")

        return True

    def get_chunks(self, memoire_id: str) -> list:
        """
        Récupère tous les chunks d'un mémoire.

        Args:
            memoire_id: UUID du mémoire

        Returns:
            Liste des chunks avec leur contenu et métadonnées
        """
        result = self.client.table('document_chunks').select('*').eq('memoire_id', memoire_id).order('created_at').execute()
        return result.data

    def get_chunk_count(self, memoire_id: str) -> int:
        """
        Compte le nombre de chunks pour un mémoire.

        Args:
            memoire_id: UUID du mémoire

        Returns:
            Nombre de chunks
        """
        result = self.client.table('document_chunks').select('id', count='exact').eq('memoire_id', memoire_id).execute()
        return result.count if result.count else 0

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

    def delete_project(self, project_id: str) -> bool:
        """
        Supprime un projet et toutes ses données associées.

        Grâce à ON DELETE CASCADE dans le schema, cela supprimera automatiquement:
        - Les sections dans sections
        - Tout document Word généré (si stocké)

        Args:
            project_id: UUID du projet à supprimer

        Returns:
            True si la suppression a réussi
        """
        # Get project to get storage paths
        project = self.get_project(project_id)
        if not project:
            return False

        # Delete RC file from storage if exists
        if project.get('rc_storage_path'):
            try:
                rc_path = project['rc_storage_path']
                self.client.storage.from_('memoires').remove([rc_path])
                print(f"✅ Deleted RC file from storage: {rc_path}")
            except Exception as e:
                print(f"⚠️ Warning: Could not delete RC file from storage: {e}")
                # Continue anyway to delete database record

        # Delete any generated Word documents from storage
        try:
            # Check if there's a generated document path (would be in projects/{id}/ folder)
            doc_path = f"projects/{project_id}/generated_memoir.docx"
            self.client.storage.from_('memoires').remove([doc_path])
            print(f"✅ Deleted generated document from storage: {doc_path}")
        except Exception as e:
            # It's OK if this fails - document might not exist yet
            print(f"ℹ️ No generated document to delete (or deletion failed): {e}")

        # Delete all files in the project folder
        try:
            project_folder = f"projects/{project_id}/"
            # List all files in project folder
            files = self.client.storage.from_('memoires').list(project_folder)
            if files:
                file_paths = [f"{project_folder}{f['name']}" for f in files]
                self.client.storage.from_('memoires').remove(file_paths)
                print(f"✅ Deleted {len(file_paths)} file(s) from project folder")
        except Exception as e:
            print(f"ℹ️ No project folder to clean up: {e}")

        # Delete database record (CASCADE will delete related sections)
        self.client.table('projects').delete().eq('id', project_id).execute()
        print(f"✅ Deleted project record and related sections: {project_id}")

        return True
