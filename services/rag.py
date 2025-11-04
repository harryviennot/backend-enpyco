"""
RAG (Retrieval Augmented Generation) Service for indexing and searching documents.

This service handles:
- Generating embeddings using OpenAI's text-embedding-3-small model
- Storing embeddings in Supabase pgvector
- Semantic search using vector similarity
"""
from typing import List, Dict, Any, Optional
from openai import OpenAI
from services.supabase import get_supabase
from config import Config


class RAGService:
    """Service for RAG operations with pgvector and OpenAI embeddings."""

    def __init__(self, openai_api_key: str = None):
        """
        Initialize the RAG service.

        Args:
            openai_api_key: OpenAI API key (defaults to Config.OPENAI_API_KEY)
        """
        self.openai_client = OpenAI(api_key=openai_api_key or Config.OPENAI_API_KEY)
        self.supabase = get_supabase()
        self.embedding_model = "text-embedding-3-small"
        self.embedding_dimension = 1536  # Dimension for text-embedding-3-small

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate an embedding vector for the given text using OpenAI.

        Args:
            text: The text to embed

        Returns:
            List of floats representing the embedding vector (1536 dimensions)

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            # Clean and truncate text if needed (OpenAI has token limits)
            # text-embedding-3-small supports up to 8191 tokens
            # Roughly 1 token = 4 characters, so ~32k chars max
            if len(text) > 32000:
                text = text[:32000]
                print(f"⚠️ Text truncated to 32k characters for embedding")

            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float"
            )

            embedding = response.data[0].embedding
            return embedding

        except Exception as e:
            print(f"❌ OpenAI embedding error: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to generate embedding: {str(e)}")

    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in a single API call.

        OpenAI allows batching up to 2048 inputs per request.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If OpenAI API call fails
        """
        try:
            if not texts:
                return []

            # OpenAI allows up to 2048 inputs per batch
            if len(texts) > 2048:
                print(f"⚠️ Batch size {len(texts)} exceeds limit, splitting into multiple batches")
                embeddings = []
                for i in range(0, len(texts), 2048):
                    batch = texts[i:i + 2048]
                    batch_embeddings = self.generate_embeddings_batch(batch)
                    embeddings.extend(batch_embeddings)
                return embeddings

            # Truncate texts if needed
            cleaned_texts = []
            for text in texts:
                if len(text) > 32000:
                    cleaned_texts.append(text[:32000])
                else:
                    cleaned_texts.append(text)

            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=cleaned_texts,
                encoding_format="float"
            )

            # Extract embeddings in the same order as input
            embeddings = [item.embedding for item in response.data]
            return embeddings

        except Exception as e:
            print(f"❌ OpenAI batch embedding error: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to generate embeddings: {str(e)}")

    def index_memoire(
        self,
        memoire_id: str,
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Generate embeddings for all chunks of a memoire and store them in pgvector.

        This method:
        1. Fetches all chunks for the memoire from the database
        2. Generates embeddings for each chunk (in batches)
        3. Updates the database with the embeddings

        Args:
            memoire_id: UUID of the memoire to index
            batch_size: Number of chunks to process in each batch (default: 100)

        Returns:
            Dictionary with indexing statistics:
                - chunks_indexed: Number of chunks that were indexed
                - embeddings_generated: Number of embeddings created
                - success: Whether the operation succeeded

        Raises:
            Exception: If indexing fails
        """
        print(f"🔍 Starting indexing for memoire: {memoire_id}")

        try:
            # Fetch all chunks for this memoire
            result = self.supabase.table('document_chunks').select('*').eq(
                'memoire_id', memoire_id
            ).execute()

            chunks = result.data
            if not chunks:
                print(f"⚠️ No chunks found for memoire {memoire_id}")
                return {
                    'chunks_indexed': 0,
                    'embeddings_generated': 0,
                    'success': True,
                    'message': 'No chunks to index'
                }

            print(f"📊 Found {len(chunks)} chunks to index")

            # Process chunks in batches to avoid overwhelming the API
            total_indexed = 0
            total_embeddings = 0

            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i + batch_size]
                batch_num = (i // batch_size) + 1
                total_batches = (len(chunks) + batch_size - 1) // batch_size

                print(f"🔄 Processing batch {batch_num}/{total_batches} ({len(batch)} chunks)")

                # Extract text content from each chunk
                texts = [chunk['content'] for chunk in batch]

                # Generate embeddings for this batch
                embeddings = self.generate_embeddings_batch(texts)

                # Update each chunk with its embedding
                for chunk, embedding in zip(batch, embeddings):
                    try:
                        # Convert embedding to pgvector format string: '[0.1,0.2,0.3,...]'
                        # Supabase Python client requires this format for vector types
                        embedding_str = '[' + ','.join(str(x) for x in embedding) + ']'

                        # Update the chunk with the embedding
                        self.supabase.table('document_chunks').update({
                            'embedding': embedding_str
                        }).eq('id', chunk['id']).execute()

                        total_indexed += 1
                        total_embeddings += 1

                    except Exception as e:
                        print(f"❌ Failed to update chunk {chunk['id']}: {e}")
                        # Continue with other chunks even if one fails

                print(f"✅ Batch {batch_num}/{total_batches} complete")

            # Mark the memoire as indexed
            self.supabase.table('memoires').update({
                'indexed': True
            }).eq('id', memoire_id).execute()

            print(f"✅ Indexing complete: {total_indexed} chunks indexed, {total_embeddings} embeddings generated")

            return {
                'chunks_indexed': total_indexed,
                'embeddings_generated': total_embeddings,
                'success': True,
                'message': f'Successfully indexed {total_indexed} chunks'
            }

        except Exception as e:
            print(f"❌ Indexing failed: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to index memoire: {str(e)}")

    def search(
        self,
        query: str,
        memoire_ids: Optional[List[str]] = None,
        n_results: int = 10,
        similarity_threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search across indexed memoires.

        Uses cosine similarity in pgvector to find the most relevant chunks.

        Args:
            query: The search query text
            memoire_ids: Optional list of memoire IDs to search within (None = search all)
            n_results: Maximum number of results to return (default: 10)
            similarity_threshold: Minimum similarity score (0.0-1.0, default: 0.0)

        Returns:
            List of dictionaries containing:
                - id: Chunk ID
                - content: The chunk text
                - metadata: Chunk metadata
                - similarity: Similarity score (0.0-1.0, higher is better)
                - memoire_id: ID of the source memoire

        Raises:
            Exception: If search fails
        """
        try:
            print(f"🔍 Searching for: '{query[:100]}...'")

            # Generate embedding for the query
            query_embedding = self.generate_embedding(query)

            # Call the PostgreSQL function for vector search
            # Function signature: match_documents(query_embedding, match_count, memoire_ids, min_similarity)
            # Note: PostgreSQL function expects parameters in specific order
            rpc_params = {
                'query_embedding': query_embedding,
                'match_count': n_results,
                'memoire_ids': memoire_ids if memoire_ids else None,
                'min_similarity': similarity_threshold
            }

            if memoire_ids:
                print(f"🎯 Filtering by memoire IDs: {memoire_ids}")

            if similarity_threshold > 0.0:
                print(f"🔍 Applying similarity threshold: {similarity_threshold}")

            # Execute the search using the match_documents RPC function
            # Filtering now happens in PostgreSQL for better performance
            result = self.supabase.rpc('match_documents', rpc_params).execute()

            search_results = result.data if result.data else []

            print(f"✅ Found {len(search_results)} results")

            return search_results

        except Exception as e:
            print(f"❌ Search failed: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to search: {str(e)}")

    def get_indexed_count(self, memoire_id: str) -> int:
        """
        Get the number of indexed chunks for a memoire.

        Args:
            memoire_id: UUID of the memoire

        Returns:
            Number of chunks with embeddings
        """
        try:
            result = self.supabase.table('document_chunks').select(
                'id',
                count='exact'
            ).eq('memoire_id', memoire_id).not_.is_('embedding', 'null').execute()

            return result.count if result.count else 0

        except Exception as e:
            print(f"❌ Failed to get indexed count: {e}")
            return 0

    def is_memoire_indexed(self, memoire_id: str) -> bool:
        """
        Check if a memoire has been fully indexed.

        Args:
            memoire_id: UUID of the memoire

        Returns:
            True if all chunks have embeddings, False otherwise
        """
        try:
            # Get total chunks
            total_result = self.supabase.table('document_chunks').select(
                'id',
                count='exact'
            ).eq('memoire_id', memoire_id).execute()

            total_chunks = total_result.count if total_result.count else 0

            if total_chunks == 0:
                return False

            # Get indexed chunks (chunks with embeddings)
            indexed_count = self.get_indexed_count(memoire_id)

            return indexed_count == total_chunks

        except Exception as e:
            print(f"❌ Failed to check if memoire is indexed: {e}")
            return False
