# Générateur Automatique de Mémoires Techniques

## 🎯 Le Problème

Chez Groupe Bernadet (BTP), répondre à un appel d'offres nécessite de rédiger un **mémoire technique** détaillé. Actuellement, ce processus prend **3 à 5 jours** par mémoire :

1. Lire le Règlement de Consultation (RC) - 20+ pages
2. Chercher dans d'anciens mémoires similaires
3. Copier-coller des sections pertinentes
4. Adapter manuellement au nouveau contexte
5. Harmoniser le format et le style
6. Relire et corriger

**Résultat** : Processus lent, répétitif et chronophage.

---

## 💡 La Solution

Une application qui **génère automatiquement** un mémoire technique personnalisé en réutilisant intelligemment le contenu d'anciens mémoires.

### Comment ça marche ?

```
┌─────────────────────────────────────────────────────────┐
│  1. PRÉPARATION (une fois)                              │
│     → Upload de 5-10 mémoires passés                    │
│     → Indexation automatique du contenu                 │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. NOUVEAU PROJET                                      │
│     → Upload du RC (Règlement de Consultation)          │
│     → Sélection de 2-3 mémoires similaires              │
│     → Choix des sections à générer                      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. GÉNÉRATION IA (3-5 minutes)                         │
│     → L'IA analyse le RC et extrait les critères       │
│     → Recherche du contenu pertinent (RAG)             │
│     → Génération section par section (Claude)          │
│     → Assemblage du document Word                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. RÉVISION (optionnel)                                │
│     → Lecture du mémoire généré                         │
│     → Régénération de sections spécifiques              │
│     → Édition manuelle si nécessaire                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. EXPORT                                              │
│     → Téléchargement du document Word final             │
│     → Style Groupe Bernadet appliqué                    │
└─────────────────────────────────────────────────────────┘
```

---

## 🔧 Technologies Clés

### 1. **RAG (Retrieval-Augmented Generation)**

- Indexe tous les anciens mémoires dans une base vectorielle
- Recherche automatiquement les passages pertinents
- Évite d'inventer des informations fausses

### 2. **Claude API (LLM)**

- Analyse le RC pour comprendre les besoins
- Génère des sections cohérentes et professionnelles
- Adapte le contenu au contexte spécifique

### 3. **Supabase (Infrastructure)**

- Base de données PostgreSQL avec pgvector
- Stockage S3 pour les fichiers
- Pas de serveur à gérer

---

## ✅ Résultats Attendus

| Aspect            | Avant     | Après        |
| ----------------- | --------- | ------------ |
| **Temps**         | 3-5 jours | 3-5 heures   |
| **Qualité**       | Variable  | Constante    |
| **Cohérence**     | Manuelle  | Automatique  |
| **Réutilisation** | Difficile | Intelligente |

**Gain de temps : 80%**

---

## 📊 Sections Générées

Le mémoire technique comprend typiquement :

1. **Présentation de l'entreprise**
   - Historique, chiffres clés, certifications
2. **Organisation du chantier**
   - Plan d'Installation de Chantier (PIC)
   - Organigramme équipe
3. **Méthodologie de réalisation**
   - Phasage des travaux
   - Techniques spécifiques
4. **Moyens humains**
   - Effectifs, qualifications
5. **Moyens matériels**
   - Liste des équipements
   - Fiches techniques
6. **Planning prévisionnel**
   - Gantt, délais
7. **Démarche environnementale**
   - RSE, gestion des déchets
8. **Sécurité et santé**
   - PPSPS, mesures de prévention
9. **Insertion sociale**
   - Heures d'insertion prévues

---

## 🎬 Exemple Concret

### Input

- **RC** : Appel d'offres SNCF pour bande d'infrastructure ferroviaire (45 pages)
- **Mémoires référence** :
  - Mémoire Toulouse Métropole 2024
  - Mémoire SNCF Bordeaux 2023
- **Sections demandées** : 8 sections

### Process

1. L'IA lit le RC et identifie : "Organisation du chantier (20 pts), Méthodologie (15 pts), Planning (10 pts)..."
2. Elle recherche dans les mémoires référence les passages sur ces sujets
3. Elle génère chaque section en adaptant au contexte SNCF
4. Elle assemble le tout en un document Word de 40 pages

### Output

- **Document Word** : 40 pages, style Bernadet
- **Temps total** : 4 heures (au lieu de 4 jours)
- **Qualité** : Professionnel, cohérent, personnalisé

---

## 🚀 MVP (Proof of Concept)

### Scope minimal

✅ Upload de mémoires référence  
✅ Upload du RC  
✅ Génération automatique (5 sections)  
✅ Export Word

❌ Interface web (API seulement)  
❌ Régénération avancée  
❌ Multi-utilisateurs

### Timeline

**7-8 jours de développement**

### Budget

~4 000€ + 25€ de crédits API

---

## 💰 ROI (Retour sur Investissement)

### Calcul

- **Gain par mémoire** : 20-35h × 50€/h = **1 000-1 750€**
- **Volume annuel** : 50 mémoires
- **Gain annuel** : **50 000-87 500€**

### Rentabilité

**Investissement** : 4 000€  
**Retour** : Dès le 3ème mémoire généré

---

## 🎯 Vision Future

### Court terme (après MVP)

- Interface web simple
- Régénération de sections
- Upload d'images/annexes

### Moyen terme

- Templates personnalisables
- Multi-utilisateurs avec permissions
- Génération d'organigrammes

### Long terme

- Génération de plannings Gantt
- Création automatique de PIC
- Assistant conversationnel intégré

---

## 🔑 Facteurs Clés de Succès

1. **Qualité du contenu généré**
   - Doit être directement utilisable
   - Pas de "hallucinations" (inventions)
2. **Facilité d'utilisation**
   - Process simple en 5 étapes
   - Pas de formation complexe nécessaire
3. **Gain de temps réel**
   - Objectif : réduire de 80% le temps
   - Permettre de répondre à plus d'appels d'offres
4. **Adoption par les utilisateurs**
   - Conducteurs de travaux doivent faire confiance au système
   - Importance du feedback pour améliorer

---

## 📝 En Résumé

**Le projet** : Un générateur automatique de mémoires techniques utilisant l'IA pour réutiliser intelligemment le contenu d'anciens mémoires.

**Le bénéfice** : Réduire de 80% le temps de rédaction tout en maintenant la qualité et la cohérence.

**La technologie** : RAG (recherche intelligente) + Claude (génération) + Supabase (infrastructure cloud).

**Le résultat** : Passer de 3-5 jours à 3-5 heures pour créer un mémoire technique professionnel.
