-- ============================================================================
-- Seed Data for Development Environment
-- ============================================================================
-- Description: Populate database with sample data for testing and development
-- Author: Claude AI Assistant
-- Date: 2025-11-06
-- Usage: Run AFTER 001_multi_tenant_schema.sql
-- WARNING: Only run in development environments!
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: COMPANY AND USERS
-- ============================================================================

-- Insert demo company
INSERT INTO companies (id, name, address, city, postal_code, phone, email, certifications, settings)
VALUES (
    '11111111-1111-1111-1111-111111111111'::UUID,
    'Enpyco Demo Company',
    '123 Construction Ave',
    'Paris',
    '75001',
    '+33 1 23 45 67 89',
    'demo@enpyco.com',
    ARRAY['ISO 9001:2015', 'QUALIBAT RGE'],
    '{"theme": "light", "language": "fr"}'::JSONB
)
ON CONFLICT (id) DO NOTHING;

-- Insert demo users (password hash is for 'password123' - bcrypt)
INSERT INTO users (id, company_id, email, password_hash, full_name, role, is_active)
VALUES
    -- Admin user
    (
        '22222222-2222-2222-2222-222222222222'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'admin@enpyco.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW.2lKNqcqGC',  -- password123
        'Admin Dupont',
        'admin',
        TRUE
    ),
    -- Regular user
    (
        '33333333-3333-3333-3333-333333333333'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'user@enpyco.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW.2lKNqcqGC',  -- password123
        'Jean Martin',
        'user',
        TRUE
    ),
    -- Viewer user
    (
        '44444444-4444-4444-4444-444444444444'::UUID,
        '11111111-1111-1111-1111-111111111111'::UUID,
        'viewer@enpyco.com',
        '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5lW.2lKNqcqGC',  -- password123
        'Marie Viewer',
        'viewer',
        TRUE
    )
ON CONFLICT (email) DO NOTHING;

-- ============================================================================
-- SECTION 2: CONTENT BLOCKS
-- ============================================================================

-- Company profile
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    '55555555-5555-5555-5555-555555555555'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'company-profile',
    'Présentation Enpyco',
    'Enpyco est une entreprise spécialisée dans les travaux de construction et de génie civil depuis 1995. Forte de plus de 25 ans d''expérience, notre équipe d''experts intervient sur des projets variés allant de la construction de bâtiments à la réalisation d''infrastructures complexes.',
    '{"founded": 1995, "employees": 50, "specialties": ["construction", "génie civil", "VRD"]}'::JSONB,
    ARRAY['présentation', 'entreprise', 'expérience'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Person CV
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    '66666666-6666-6666-6666-666666666666'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'person-cv',
    'CV - Pierre Dupont - Ingénieur Travaux',
    'Pierre Dupont, Ingénieur diplômé de l''École des Ponts ParisTech (2010), possède 13 ans d''expérience dans la conduite de chantiers. Spécialisé dans les ouvrages d''art, il a dirigé plus de 20 projets majeurs.',
    '{"degree": "Ingénieur Ponts", "experience_years": 13, "certifications": ["CSPS"]}'::JSONB,
    ARRAY['ingénieur', 'travaux', 'ouvrages d''art'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Equipment
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    '77777777-7777-7777-7777-777777777777'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'equipment',
    'Pelle hydraulique Caterpillar 336',
    'Pelle hydraulique Caterpillar 336FL, année 2020, équipée d''un godet de 1,8 m³. Masse opérationnelle : 36 tonnes. Profondeur de fouille maximale : 7,3 m. Moteur diesel Cat C9.3B de 313 CV.',
    '{"brand": "Caterpillar", "model": "336FL", "year": 2020, "power_hp": 313}'::JSONB,
    ARRAY['pelle', 'terrassement', 'caterpillar'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Procedure
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    '88888888-8888-8888-8888-888888888888'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'procedure',
    'Procédure de bétonnage par temps froid',
    'En période hivernale (température < 5°C), les précautions suivantes doivent être prises : 1) Chauffer les agrégats et l''eau de gâchage, 2) Utiliser un ciment adapté (CEM I), 3) Protéger le béton frais avec des bâches isolantes, 4) Maintenir une température minimale de 10°C pendant 3 jours.',
    '{"season": "hiver", "min_temp": 5, "cure_days": 3}'::JSONB,
    ARRAY['bétonnage', 'hiver', 'température'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Certification
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    '99999999-9999-9999-9999-999999999999'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'certification',
    'Certification QUALIBAT 2523',
    'Enpyco est titulaire de la qualification QUALIBAT 2523 - Travaux de terrassement - catégorie jusqu''à 3 000 000 €. Certificat obtenu en 2018, renouvelé en 2022, valable jusqu''en 2026.',
    '{"number": "2523", "category": "terrassement", "valid_until": "2026-12-31"}'::JSONB,
    ARRAY['qualibat', 'terrassement', 'certification'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Methodology template
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'methodology-template',
    'Méthodologie de terrassement en tranchée',
    'Phase 1 : Préparation - Implantation et piquetage. Phase 2 : Terrassement - Excavation par passes de 50 cm. Phase 3 : Blindage - Pose des blindages selon profondeur. Phase 4 : Contrôles - Vérification dimensions et nivellement.',
    '{"phases": 4, "max_depth": "6m", "equipment": ["pelle", "blindage"]}'::JSONB,
    ARRAY['méthodologie', 'terrassement', 'tranchée'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- Past project reference
INSERT INTO content_blocks (id, company_id, type, title, content, metadata, tags, created_by)
VALUES (
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'past-project-reference',
    'Référence : Réseau VRD Lotissement Les Érables',
    'Réalisation complète des VRD d''un lotissement de 45 lots à Meudon (92). Travaux : terrassement (2 500 m³), voirie (1 200 ml), réseaux EU/EP/AEP. Durée : 8 mois. Montant : 850 000 € HT.',
    '{"client": "Ville de Meudon", "year": 2022, "amount": 850000, "duration_months": 8}'::JSONB,
    ARRAY['VRD', 'lotissement', 'référence'],
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SECTION 3: PAST PROJECTS
-- ============================================================================

INSERT INTO past_projects (id, company_id, name, client, year, project_type, description, techniques_used, success_factors, is_referenceable, created_by)
VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'Construction Parking Souterrain Centre-Ville',
    'Mairie de Versailles',
    2021,
    'Génie Civil',
    'Construction d''un parking souterrain de 250 places sur 2 niveaux. Parois moulées, excavation blindée, dalle béton armé.',
    ARRAY['parois moulées', 'excavation blindée', 'béton armé', 'étanchéité'],
    ARRAY['Respect délais malgré conditions hydrogéologiques complexes', 'Coordination avec autres corps d''état', 'Zéro accident'],
    TRUE,
    '22222222-2222-2222-2222-222222222222'::UUID
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SECTION 4: SECTION TEMPLATES
-- ============================================================================

INSERT INTO section_templates (id, company_id, section_type, title, template_content, placeholders)
VALUES (
    'dddddddd-dddd-dddd-dddd-dddddddddddd'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'présentation-entreprise',
    'Présentation de l''entreprise',
    'La société {{company_name}}, basée à {{city}}, intervient depuis {{years}} ans dans le domaine de {{specialty}}. Nous disposons de {{certifications}} et d''une équipe de {{team_size}} collaborateurs qualifiés.',
    '{"company_name": "Nom de l''entreprise", "city": "Ville", "years": "Nombre d''années", "specialty": "Spécialité", "certifications": "Certifications", "team_size": "Taille équipe"}'::JSONB
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SECTION 5: SAMPLE PROJECT
-- ============================================================================

-- Insert a sample project
INSERT INTO projects (id, company_id, name, rc_storage_path, status, created_by, client, location, lot, project_type)
VALUES (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'::UUID,
    '11111111-1111-1111-1111-111111111111'::UUID,
    'Mémoire Technique - Travaux VRD Lotissement Bellevue',
    'projects/demo/rc_bellevue.pdf',
    'draft',
    '22222222-2222-2222-2222-222222222222'::UUID,
    'Promoteur Bellevue SAS',
    'Boulogne-Billancourt',
    'Lot 01 - VRD',
    'VRD'
)
ON CONFLICT (id) DO NOTHING;

-- ============================================================================
-- SECTION 6: AUDIT LOG SAMPLES
-- ============================================================================

INSERT INTO audit_log (action, user_id, resource_type, resource_id, details)
VALUES
    ('user.login', '22222222-2222-2222-2222-222222222222'::UUID, 'user', '22222222-2222-2222-2222-222222222222'::UUID, '{"method": "email"}'::JSONB),
    ('project.create', '22222222-2222-2222-2222-222222222222'::UUID, 'project', 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'::UUID, '{"project_name": "Mémoire Technique - Travaux VRD Lotissement Bellevue"}'::JSONB),
    ('content_block.create', '22222222-2222-2222-2222-222222222222'::UUID, 'content_block', '55555555-5555-5555-5555-555555555555'::UUID, '{"type": "company-profile"}'::JSONB)
ON CONFLICT DO NOTHING;

COMMIT;

-- ============================================================================
-- SEED DATA COMPLETE
-- ============================================================================
-- Created:
-- - 1 demo company (Enpyco Demo Company)
-- - 3 demo users (admin, user, viewer) - password: password123
-- - 7 content blocks (one of each type)
-- - 1 past project
-- - 1 section template
-- - 1 sample project
-- - 3 audit log entries
-- ============================================================================
-- Login credentials:
-- - admin@enpyco.com / password123
-- - user@enpyco.com / password123
-- - viewer@enpyco.com / password123
-- ============================================================================
