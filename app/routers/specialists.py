from fastapi import APIRouter, HTTPException, Query
from datetime import date

router = APIRouter(
    prefix="/api/v1/specialists",
    tags=["Specialists"]
)

# Mock data
SPECIALISTS = [
    {
        "id": "spec_001",
        "name": "Dr. Sarah Lim",
        "specialty": "Cardiology",
        "imagePath": "assets/images/specialists/cardiology_1.jpg",
        "bio": "Experienced cardiologist focused on hypertension, heart rhythm monitoring, and preventive cardiovascular care.",
        "experienceYears": 12,
        "careerPath": [
            "MBBS - University of Malaya",
            "Internal Medicine Residency - Kuala Lumpur General Hospital",
            "Cardiology Fellowship - National Heart Institute"
        ],
        "highlights": [
            "Hypertension management",
            "Cardiac risk assessment",
            "Remote heart-rate monitoring"
        ]
    },
    {
        "id": "spec_002",
        "name": "Dr. Jason Tan",
        "specialty": "Endocrinology",
        "imagePath": "assets/images/specialists/endocrinology_1.jpg",
        "bio": "Endocrinologist specializing in diabetes management, glucose control, and metabolic health.",
        "experienceYears": 10,
        "careerPath": [
            "MD - Monash University Malaysia",
            "Internal Medicine Training - Penang General Hospital",
            "Endocrinology Fellowship - Singapore"
        ],
        "highlights": [
            "Diabetes care plans",
            "Blood glucose optimization",
            "Lifestyle and metabolic counseling"
        ]
    },
    {
        "id": "spec_003",
        "name": "Dr. Aina Rahman",
        "specialty": "Pulmonology",
        "imagePath": "assets/images/specialists/pulmonology_1.jpg",
        "bio": "Pulmonologist interested in oxygen saturation trends, respiratory symptoms, and long-term lung health.",
        "experienceYears": 8,
        "careerPath": [
            "MBBS - International Medical University",
            "Respiratory Medicine Training - Selayang Hospital"
        ],
        "highlights": [
            "Respiratory monitoring",
            "Oxygen saturation review",
            "Sleep and breathing assessment"
        ]
    },
    {
        "id": "spec_004",
        "name": "Dr. Mei Wong",
        "specialty": "Sleep Medicine",
        "imagePath": "assets/images/specialists/sleep_1.jpg",
        "bio": "Sleep medicine specialist supporting sleep quality improvement and long-term behavioral sleep care.",
        "experienceYears": 9,
        "careerPath": [
            "MD - University of Nottingham Malaysia",
            "Neurology Rotation - Johor Specialist Center",
            "Sleep Medicine Certification"
        ],
        "highlights": [
            "Sleep duration analysis",
            "Sleep hygiene planning",
            "Behavioral sleep support"
        ]
    }
]

#mock availability
SPECIALIST_AVAILABILITY = {
    "spec_001": ["09:00", "11:00", "14:30"],
    "spec_002": ["10:00", "13:00", "16:00"],
    "spec_003": ["09:30", "12:00", "15:30"],
    "spec_004": ["08:30", "11:30", "17:00"],
}


@router.get("")
def get_specialists(search: str | None = Query(None)):
    query = (search or "").strip().lower()

    if not query:
        result = [
            {
                "id": s["id"],
                "name": s["name"],
                "specialty": s["specialty"],
                "imagePath": s["imagePath"]
            }
            for s in SPECIALISTS
        ]
    else:
        result = [
            {
                "id": s["id"],
                "name": s["name"],
                "specialty": s["specialty"],
                "imagePath": s["imagePath"]
            }
            for s in SPECIALISTS
            if query in s["name"].lower()
            or query in s["specialty"].lower()
            or query in s["id"].lower()
        ]

    return {
        "status": "success",
        "count": len(result),
        "data": result
    }


@router.get("/{id}")
def get_specialist_detail(id: str):
    specialist = next((s for s in SPECIALISTS if s["id"] == id), None)

    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    return {
        "status": "success",
        "data": specialist
    }


@router.get("/{id}/availability")
def get_specialist_availability(id: str, date: date = Query(...)):
    specialist = next((s for s in SPECIALISTS if s["id"] == id), None)

    if not specialist:
        raise HTTPException(status_code=404, detail="Specialist not found")

    #mock logic:
    # weekends -> fewer / no slots
    weekday = date.weekday()  # Mon=0 ... Sun=6

    if weekday == 6:
        slots = []
    elif weekday == 5:
        slots = ["10:00", "12:00"]
    else:
        slots = SPECIALIST_AVAILABILITY.get(id, [])

    return {
        "status": "success",
        "date": date.isoformat(),
        "data": slots
    }