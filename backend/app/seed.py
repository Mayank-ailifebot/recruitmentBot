"""
RecruitBot — Synthetic Seed Data Generator (Sprint 0.2)

Generates realistic fake data for:
- 10 Top-Performing Employees (with Career DNA embeddings)
- 30 Candidates (mix of silver medalists, qualified, and unqualified)
- 3 Job Requisitions
- Applications linking candidates to jobs
- Consent records for each candidate

Embeddings are mathematically valid normalized vectors (1024-dim)
so pgvector similarity queries work out of the box.

Usage: python -m app.seed
"""

import uuid
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, SYNC_DATABASE_URL
from app.models import (
    Employee,
    Candidate,
    JobRequisition,
    Application,
    Resume,
    FitScore,
    Consent,
    AuditLog,
    VECTOR_DIMENSIONS,
)

# ── Seed configuration ──
NUM_TOP_EMPLOYEES = 10
NUM_CANDIDATES = 30
NUM_SILVER_MEDALISTS = 5
NUM_REQUISITIONS = 3

# ── Realistic data pools ──
DEPARTMENTS = ["AI & Machine Learning", "Enterprise Sales", "Product Engineering", "Data Science", "Customer Success"]

ROLES_BY_DEPT = {
    "AI & Machine Learning": ["ML Engineer", "AI Research Lead", "MLOps Engineer", "NLP Specialist"],
    "Enterprise Sales": ["Enterprise Account Executive", "Sales Director", "Business Development Lead", "Solutions Architect"],
    "Product Engineering": ["Senior Backend Engineer", "Full Stack Developer", "Platform Engineer", "Engineering Manager"],
    "Data Science": ["Senior Data Scientist", "Analytics Lead", "Data Engineer", "Quantitative Analyst"],
    "Customer Success": ["Customer Success Manager", "Technical Account Manager", "Onboarding Specialist", "Support Engineer"],
}

COMPANIES = [
    "Infosys", "TCS", "Wipro", "HCL Technologies", "Tech Mahindra",
    "Flipkart", "Razorpay", "CRED", "Zerodha", "PhonePe",
    "Google India", "Microsoft India", "Amazon India", "Adobe India",
    "Goldman Sachs India", "Morgan Stanley India", "JP Morgan India",
    "Reliance Jio", "Bharti Airtel", "HDFC Bank",
    "Zomato", "Swiggy", "Ola", "Paytm", "Freshworks",
]

EDUCATION = [
    "IIT Bombay - B.Tech Computer Science",
    "IIT Delhi - B.Tech Electrical Engineering",
    "IIM Ahmedabad - MBA",
    "IIM Bangalore - PGDM",
    "BITS Pilani - M.Tech",
    "NIT Trichy - B.Tech",
    "DTU Delhi - B.Tech",
    "ISI Kolkata - M.Stat",
    "IISC Bangalore - M.Tech ML",
    "VIT Vellore - B.Tech",
    "Manipal University - B.Tech",
    "SRM University - B.Tech",
    "Christ University - BBA",
    "Symbiosis - MBA",
    "XLRI Jamshedpur - MBA HR",
]

SKILLS_POOL = [
    "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "PostgreSQL", "MongoDB", "Redis", "Docker", "Kubernetes",
    "AWS", "GCP", "Azure", "Terraform", "CI/CD",
    "Data Analysis", "SQL", "Spark", "Kafka", "Airflow",
    "Leadership", "Team Management", "Strategic Planning", "Sales Strategy",
    "CRM", "Salesforce", "HubSpot", "Negotiation", "Client Relations",
]

LOCATIONS = [
    "Mumbai, Maharashtra", "Bangalore, Karnataka", "Delhi NCR",
    "Hyderabad, Telangana", "Pune, Maharashtra", "Chennai, Tamil Nadu",
    "Gurgaon, Haryana", "Noida, Uttar Pradesh", "Kolkata, West Bengal",
    "Ahmedabad, Gujarat",
]

FIRST_NAMES = [
    "Aarav", "Aditi", "Arjun", "Priya", "Rohan", "Sneha", "Vikram", "Ananya",
    "Rahul", "Neha", "Karthik", "Divya", "Amit", "Pooja", "Siddharth",
    "Meera", "Varun", "Ishita", "Nikhil", "Kavita", "Raj", "Shruti",
    "Deepak", "Tanvi", "Harsh", "Riya", "Manish", "Sanya", "Aakash", "Nisha",
    "Suresh", "Lakshmi", "Ganesh", "Anjali", "Pranav", "Swati",
]

LAST_NAMES = [
    "Sharma", "Patel", "Kumar", "Singh", "Gupta", "Mehta", "Joshi",
    "Verma", "Reddy", "Nair", "Iyer", "Rao", "Desai", "Shah",
    "Agarwal", "Malhotra", "Chopra", "Banerjee", "Ghosh", "Dutta",
    "Kapoor", "Tiwari", "Srinivasan", "Bhat", "Pillai", "Menon",
]

PROFESSIONAL_SUMMARIES = [
    "Results-driven {role} with {years}+ years of experience building scalable systems at top Indian tech companies. Passionate about leveraging AI to drive business outcomes.",
    "Seasoned {role} specializing in high-growth enterprise environments. Led cross-functional teams of 15+ engineers to deliver mission-critical platforms.",
    "Dynamic {role} with deep expertise in full-stack development and cloud-native architectures. Proven track record of reducing infrastructure costs by 40%.",
    "Strategic {role} with expertise in consultative selling to Fortune 500 clients across BFSI and healthcare verticals. Consistently exceeded quota by 130%+.",
    "Analytical {role} combining technical depth with business acumen. Published research in NeurIPS and applied ML solutions driving $2M+ in annual revenue.",
]


def generate_normalized_vector(seed_offset: int = 0, cluster: str = "general") -> list:
    """
    Generate a mathematically valid, normalized 1024-dim vector.

    Uses cluster-based generation so that:
    - Top performers in the same department cluster together
    - Silver medalists are close (but not identical) to top performers
    - Random candidates have more spread
    """
    rng = np.random.RandomState(seed_offset)

    # Base vector
    vec = rng.randn(VECTOR_DIMENSIONS).astype(np.float32)

    # Add cluster bias so similar roles cluster in vector space
    cluster_seeds = {
        "top_performer_tech": 42,
        "top_performer_sales": 84,
        "silver_medalist": 42,  # Close to tech top performers
        "qualified": 100,
        "unqualified": 200,
        "general": 0,
    }

    cluster_seed = cluster_seeds.get(cluster, 0)
    if cluster_seed:
        cluster_rng = np.random.RandomState(cluster_seed)
        cluster_bias = cluster_rng.randn(VECTOR_DIMENSIONS).astype(np.float32)
        # Mix: 60% cluster direction + 40% individual variation
        weight = 0.6 if cluster in ("top_performer_tech", "top_performer_sales", "silver_medalist") else 0.3
        vec = weight * cluster_bias + (1 - weight) * vec

    # Normalize to unit vector (required for cosine similarity)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm

    return vec.tolist()


def create_employees(session) -> list:
    """Create 10 top-performing employees across departments."""
    employees = []
    used_names = set()

    for i in range(NUM_TOP_EMPLOYEES):
        dept = DEPARTMENTS[i % len(DEPARTMENTS)]
        roles = ROLES_BY_DEPT[dept]
        role = random.choice(roles)

        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            if (first, last) not in used_names:
                used_names.add((first, last))
                break

        years = random.randint(4, 12)
        cluster = "top_performer_tech" if "Engineer" in role or "ML" in role or "Data" in role else "top_performer_sales"

        emp = Employee(
            id=uuid.uuid4(),
            email=f"{first.lower()}.{last.lower()}@company.internal",
            first_name=first,
            last_name=last,
            department=dept,
            role=role,
            hire_date=datetime.now(timezone.utc) - timedelta(days=years * 365),
            tenure_months=years * 12,
            performance_rating=round(random.uniform(4.2, 5.0), 1),
            promotion_count=random.randint(1, 4),
            previous_companies=random.sample(COMPANIES, k=random.randint(2, 4)),
            education=random.choice(EDUCATION),
            professional_summary=random.choice(PROFESSIONAL_SUMMARIES).format(role=role, years=years),
            embedding=generate_normalized_vector(seed_offset=i * 7, cluster=cluster),
            is_top_performer=True,
            is_active=True,
        )
        session.add(emp)
        employees.append(emp)

    print(f"  ✅ Created {len(employees)} top-performing employees")
    return employees


def create_candidates(session) -> list:
    """Create 30 candidates: 5 silver medalists + 15 qualified + 10 unqualified."""
    candidates = []
    used_names = set()

    for i in range(NUM_CANDIDATES):
        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            if (first, last) not in used_names:
                used_names.add((first, last))
                break

        # Determine candidate tier
        if i < NUM_SILVER_MEDALISTS:
            source = "silver_medalist"
            years_exp = random.randint(5, 10)
            cluster = "silver_medalist"
        elif i < NUM_SILVER_MEDALISTS + 15:
            source = "direct"
            years_exp = random.randint(3, 8)
            cluster = "qualified"
        else:
            source = "direct"
            years_exp = random.randint(0, 3)
            cluster = "unqualified"

        candidate = Candidate(
            id=uuid.uuid4(),
            email=f"{first.lower()}.{last.lower()}{random.randint(1,99)}@gmail.com",
            first_name=first,
            last_name=last,
            phone=f"+91 {random.randint(70000, 99999)} {random.randint(10000, 99999)}",
            current_company=random.choice(COMPANIES),
            current_role=random.choice(sum(ROLES_BY_DEPT.values(), [])),
            years_experience=years_exp,
            location=random.choice(LOCATIONS),
            linkedin_url=f"https://linkedin.com/in/{first.lower()}-{last.lower()}-{random.randint(100,999)}",
            source=source,
            is_active=True,
        )
        session.add(candidate)

        # Create a resume for each candidate
        skills = random.sample(SKILLS_POOL, k=random.randint(4, 10))
        resume = Resume(
            id=uuid.uuid4(),
            candidate_id=candidate.id,
            raw_text=f"Experienced {candidate.current_role} with {years_exp} years at {candidate.current_company}. Skills: {', '.join(skills)}.",
            file_format="pdf",
            parsed_json={
                "skills": skills,
                "roles": [{"title": candidate.current_role, "company": candidate.current_company, "years": years_exp}],
                "education": [random.choice(EDUCATION)],
                "certifications": random.sample(["AWS Certified", "GCP Professional", "PMP", "Scrum Master", "CFA Level 1"], k=random.randint(0, 2)),
            },
            parse_confidence=round(random.uniform(0.85, 0.99), 2),
            embedding=generate_normalized_vector(seed_offset=100 + i * 11, cluster=cluster),
        )
        session.add(resume)

        # Create consent records
        for consent_type in ["data_storage", "sourcing_matching", "ai_interviewing"]:
            consent = Consent(
                id=uuid.uuid4(),
                candidate_id=candidate.id,
                consent_type=consent_type,
                status=True,
                granted_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 30)),
            )
            session.add(consent)

        candidates.append(candidate)

    print(f"  ✅ Created {len(candidates)} candidates ({NUM_SILVER_MEDALISTS} silver medalists)")
    return candidates


def create_requisitions(session) -> list:
    """Create 3 active job requisitions."""
    reqs_data = [
        {
            "title": "Senior ML Engineer",
            "department": "AI & Machine Learning",
            "brief": "We need a senior ML engineer to lead our recommendation system. Must have production ML experience, Python, and cloud deployment. Someone who can mentor juniors.",
            "skills": ["Python", "Machine Learning", "Deep Learning", "AWS", "Docker", "Kubernetes"],
            "location": "Bangalore, Karnataka",
            "salary": "₹35-50 LPA",
        },
        {
            "title": "Enterprise Account Executive",
            "department": "Enterprise Sales",
            "brief": "Looking for a hunter who can close large BFSI deals. Must have a strong rolodex in banking/insurance sector. Consultative selling approach essential.",
            "skills": ["Sales Strategy", "CRM", "Salesforce", "Negotiation", "Client Relations", "Strategic Planning"],
            "location": "Mumbai, Maharashtra",
            "salary": "₹25-40 LPA + Commission",
        },
        {
            "title": "Full Stack Developer",
            "department": "Product Engineering",
            "brief": "Need a strong full-stack dev for our AI recruitment platform. React + Python/FastAPI stack. Experience with real-time systems and AI integrations is a plus.",
            "skills": ["React", "TypeScript", "Python", "FastAPI", "PostgreSQL", "Docker"],
            "location": "Delhi NCR",
            "salary": "₹20-35 LPA",
        },
    ]

    requisitions = []
    for i, data in enumerate(reqs_data):
        req = JobRequisition(
            id=uuid.uuid4(),
            title=data["title"],
            department=data["department"],
            raw_brief=data["brief"],
            generated_jd=None,  # Will be generated by LLM in Sprint 1.1
            requirements_json={"min_experience": 4, "education": "B.Tech/M.Tech preferred"},
            skills_required=data["skills"],
            archetype_embedding=generate_normalized_vector(seed_offset=200 + i * 13, cluster="top_performer_tech"),
            posting_channels=[
                {"channel": "Naukri", "status": "simulated"},
                {"channel": "LinkedIn", "status": "simulated"},
                {"channel": "Indeed", "status": "simulated"},
            ],
            status="active",
            location=data["location"],
            salary_range=data["salary"],
        )
        session.add(req)
        requisitions.append(req)

    print(f"  ✅ Created {len(requisitions)} job requisitions")
    return requisitions


def create_applications(session, candidates: list, requisitions: list) -> list:
    """Link candidates to requisitions with varying pipeline statuses."""
    applications = []
    statuses = ["applied", "screening", "interviewing", "shortlisted", "rejected"]

    for req in requisitions:
        # Assign 8-12 candidates per requisition
        num_applicants = random.randint(8, 12)
        selected_candidates = random.sample(candidates, k=min(num_applicants, len(candidates)))

        for j, candidate in enumerate(selected_candidates):
            is_sm = candidate.source == "silver_medalist"
            status = "shortlisted" if is_sm else random.choice(statuses)

            app = Application(
                id=uuid.uuid4(),
                candidate_id=candidate.id,
                requisition_id=req.id,
                status=status,
                source=candidate.source,
                is_silver_medalist=is_sm,
                applied_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 14)),
            )
            session.add(app)

            # Create a fit score for screened+ candidates
            if status in ("screening", "interviewing", "shortlisted"):
                hard = round(random.uniform(50, 95), 1) if not is_sm else round(random.uniform(75, 95), 1)
                exp = round(random.uniform(40, 95), 1) if not is_sm else round(random.uniform(70, 95), 1)
                behav = round(random.uniform(45, 90), 1) if not is_sm else round(random.uniform(65, 90), 1)
                total = round(hard * 0.3 + exp * 0.4 + behav * 0.3, 1)

                score = FitScore(
                    id=uuid.uuid4(),
                    application_id=app.id,
                    hard_skills_score=hard,
                    experience_quality_score=exp,
                    behavioral_intent_score=behav,
                    total_score=total,
                    rationale_json={
                        "hard_skills": f"Candidate demonstrates {'strong' if hard > 70 else 'moderate'} technical proficiency.",
                        "experience": f"{'Highly relevant' if exp > 70 else 'Partially relevant'} prior experience.",
                        "behavioral": f"Career narrative indicates {'strong growth orientation' if behav > 70 else 'mixed intent'}.",
                    },
                    is_anonymized=True,
                )
                session.add(score)

            applications.append(app)

    print(f"  ✅ Created {len(applications)} applications with fit scores")
    return applications


def run_seed():
    """Main seed execution."""
    print("\n🌱 RecruitBot Seed Generator")
    print("=" * 50)

    # Use sync engine for seeding
    engine = create_engine(SYNC_DATABASE_URL, echo=False)

    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Clear existing data (in reverse FK order)
        print("\n🗑️  Clearing existing data...")
        for table in ["audit_log", "fit_scores", "interviews", "consent", "resumes", "applications", "candidates", "employees", "job_requisitions"]:
            session.execute(text(f"DELETE FROM {table}"))
        session.commit()
        print("  ✅ Cleared all tables")

        # Seed
        print("\n📊 Generating seed data...")
        random.seed(42)  # Reproducible
        np.random.seed(42)

        employees = create_employees(session)
        candidates = create_candidates(session)
        requisitions = create_requisitions(session)
        applications = create_applications(session, candidates, requisitions)

        session.commit()

        # Verification
        print("\n🔍 Verifying seed data...")
        for table in ["employees", "candidates", "job_requisitions", "applications", "resumes", "fit_scores", "consent"]:
            count = session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
            print(f"  📋 {table}: {count} rows")

        # Vector similarity sanity test
        print("\n🧮 Running pgvector similarity sanity test...")
        result = session.execute(text("""
            SELECT e.first_name, e.last_name, e.role,
                   1 - (e.embedding <=> r.embedding) AS similarity
            FROM employees e
            CROSS JOIN resumes r
            WHERE e.is_top_performer = true
            AND e.embedding IS NOT NULL
            AND r.embedding IS NOT NULL
            ORDER BY e.embedding <=> r.embedding
            LIMIT 5
        """))
        print("  Top 5 employee-resume similarity matches:")
        for row in result:
            print(f"    👤 {row[0]} {row[1]} ({row[2]}) → similarity: {row[3]:.4f}")

        print("\n✅ Seed complete! Database is ready for development.")

    except Exception as e:
        session.rollback()
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run_seed()
