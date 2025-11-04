"""
Service for generating memoir sections using Claude API.
"""
from anthropic import Anthropic
from typing import List, Dict, Optional
from services.supabase import SupabaseService
from services.rag import RAGService
from config import Config


class GeneratorService:
    """Service for generating memoir sections using Claude API."""

    # Section type descriptions in French
    SECTION_DESCRIPTIONS = {
        'presentation': 'Présentation de l\'entreprise (historique, chiffres clés, certifications)',
        'organisation': 'Organisation du chantier (PIC, moyens, logistique)',
        'methodologie': 'Méthodologie de réalisation (phasage, techniques)',
        'moyens_humains': 'Moyens humains (organigramme, effectifs)',
        'moyens_materiels': 'Moyens matériels (liste équipements, capacités)',
        'planning': 'Planning prévisionnel (Gantt, délais)',
        'environnement': 'Démarche environnementale (RSE, gestion des déchets)',
        'securite': 'Sécurité et santé (PPSPS, mesures de prévention)',
        'insertion': 'Insertion sociale (heures d\'insertion prévues)'
    }

    def __init__(self, api_key: str = None):
        """
        Initialize the generator service with Claude client.

        Args:
            api_key: Claude API key (defaults to Config.CLAUDE_API_KEY)
        """
        self.client = Anthropic(api_key=api_key or Config.CLAUDE_API_KEY)
        self.supabase = SupabaseService()
        self.rag = RAGService()
        self.model = "claude-sonnet-4-20250514"  # Latest Sonnet 4.5

        print(f"✅ GeneratorService initialized with model: {self.model}")

    def generate_section(
        self,
        section_type: str,
        rc_context: str,
        reference_chunks: List[Dict],
        max_tokens: int = 4096,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a memoir section using Claude API.

        Args:
            section_type: Type of section to generate (e.g., 'presentation', 'organisation')
            rc_context: Context extracted from RC document
            reference_chunks: List of similar chunks from RAG search
            max_tokens: Maximum tokens for generation (default: 4096)
            temperature: Temperature for generation (default: 0.7)

        Returns:
            Generated markdown content

        Raises:
            Exception: If generation fails
        """
        print(f"📝 Generating section: {section_type}")
        print(f"   Section description: {self.SECTION_DESCRIPTIONS.get(section_type, 'N/A')}")

        try:
            # Build prompt
            print(f"   🔨 Building prompt...")
            prompt = self._build_prompt(section_type, rc_context, reference_chunks)

            # Log prompt size
            print(f"   ✅ Prompt built: ~{len(prompt)} characters")
            print(f"   📚 Reference chunks: {len(reference_chunks)}")
            print(f"   📄 RC context: {len(rc_context)} characters")

            # Call Claude API
            print(f"   🤖 Calling Claude API (model: {self.model})...")
            print(f"   ⏳ This may take 20-60 seconds...")

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract content
            content = response.content[0].text

            print(f"✅ Section '{section_type}' generated successfully!")
            print(f"   📊 Content length: {len(content)} characters")
            print(f"   💰 Tokens used: {response.usage.input_tokens} in / {response.usage.output_tokens} out")
            print(f"   ⏱️  Total tokens: {response.usage.input_tokens + response.usage.output_tokens}")

            return content

        except Exception as e:
            print(f"❌ Generation failed for section '{section_type}'")
            print(f"   Error type: {type(e).__name__}")
            print(f"   Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            raise Exception(f"Failed to generate section '{section_type}': {str(e)}")

    def extract_rc_criteria(self, rc_text: str, max_tokens: int = 500) -> str:
        """
        Extract key criteria from RC document using Claude.

        This helps understand what the client is looking for in the memoir.

        Args:
            rc_text: Full or partial text from RC document
            max_tokens: Maximum tokens for extraction (default: 500)

        Returns:
            Extracted criteria as text

        Raises:
            Exception: If extraction fails
        """
        print(f"🔍 Extracting RC criteria")
        print(f"   RC text size: {len(rc_text)} characters")

        try:
            # Limit RC text to avoid token limits (take first 3000 chars)
            rc_sample = rc_text[:3000] if len(rc_text) > 3000 else rc_text

            prompt = f"""Analyse ce Règlement de Consultation et extrait les critères d'évaluation principaux du mémoire technique.

RC :
{rc_sample}

Liste uniquement les 5-7 critères les plus importants, de manière concise."""

            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for extraction
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            criteria = response.content[0].text

            print(f"✅ Criteria extracted: {len(criteria)} characters")

            return criteria

        except Exception as e:
            print(f"❌ Criteria extraction failed: {type(e).__name__}: {str(e)}")
            raise Exception(f"Failed to extract RC criteria: {str(e)}")

    def _build_prompt(
        self,
        section_type: str,
        rc_context: str,
        reference_chunks: List[Dict]
    ) -> str:
        """
        Build the prompt for Claude API.

        Args:
            section_type: Type of section to generate
            rc_context: Context from RC document
            reference_chunks: List of reference chunks with 'content' and 'similarity'

        Returns:
            Formatted prompt string
        """
        # Get section description
        description = self.SECTION_DESCRIPTIONS.get(
            section_type,
            section_type.replace('_', ' ').title()
        )

        # Format reference chunks (top 5 by similarity)
        references_text = ""
        if reference_chunks:
            # Sort by similarity (descending) and take top 5
            sorted_chunks = sorted(
                reference_chunks,
                key=lambda x: x.get('similarity', 0),
                reverse=True
            )[:5]

            references_list = []
            for i, chunk in enumerate(sorted_chunks, 1):
                similarity = chunk.get('similarity', 0)
                content = chunk.get('content', '')
                metadata = chunk.get('metadata', {})
                filename = metadata.get('filename', 'Unknown')

                references_list.append(
                    f"Extrait de référence {i} (similarité: {similarity:.2f}, source: {filename}):\n{content}"
                )

            references_text = "\n\n---\n\n".join(references_list)
        else:
            references_text = "Aucune référence disponible. Génère du contenu basé sur les meilleures pratiques du BTP."

        # Format RC context
        rc_text = rc_context if rc_context else "Projet de construction (contexte non disponible)"

        # Build the full prompt
        prompt = f"""Tu es un expert en rédaction de mémoires techniques pour le BTP (Bâtiment et Travaux Publics).

**Contexte du projet (extrait du Règlement de Consultation) :**
{rc_text}

**Type de section à générer :** {description}

**Contenu de référence (extraits de mémoires similaires) :**
{references_text}

**Instructions :**
1. Génère une section professionnelle de mémoire technique
2. Réutilise les informations factuelles des références (chiffres, méthodes, équipements, certifications)
3. Adapte le contenu au contexte spécifique du RC
4. Utilise un ton professionnel mais accessible
5. Privilégie les tableaux aux longues listes quand c'est pertinent
6. Structure : titre H2, sous-titres H3, paragraphes clairs
7. Utilise des bullet points pour les listes d'éléments

**Contraintes :**
- Format : Markdown
- Longueur : 500-1000 mots
- Ne pas inventer de données chiffrées, utiliser uniquement les références
- Si une information n'est pas dans les références, reste générique et professionnel
- Adapte les noms d'entreprise, projets, et dates au contexte du RC

Génère maintenant la section :"""

        return prompt

    def get_valid_section_types(self) -> List[str]:
        """
        Get list of valid section types.

        Returns:
            List of section type identifiers
        """
        return list(self.SECTION_DESCRIPTIONS.keys())

    def validate_section_type(self, section_type: str) -> bool:
        """
        Check if a section type is valid.

        Args:
            section_type: Section type to validate

        Returns:
            True if valid, False otherwise
        """
        return section_type in self.SECTION_DESCRIPTIONS
