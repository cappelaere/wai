# Schema Examples for Agent Prompts

This document contains two realistic examples for each agent schema that can be used to improve LLM output quality by providing concrete examples in agent prompts.

## Personal Agent Schema Examples

### Example 1: Strong Aviation-Focused Applicant

```json
{
  "summary": "Sarah demonstrates deep passion for aviation through both her academic pursuits and community involvement. With clear career goals to become a commercial pilot and active leadership in her school's aerospace club, she shows strong alignment with WAI's mission. Her persistence in pursuing flight training while maintaining excellent grades, combined with her commitment to mentoring younger students, indicates both dedication and character.",
  "profile_features": {
    "motivation_summary": "Sarah's passion for aviation began at age 12 when her uncle took her flying. She has since earned her private pilot license and is actively working toward her commercial license while maintaining a 3.8 GPA in aerospace engineering.",
    "career_goals_summary": "Sarah aspires to become a commercial airline pilot, with a long-term goal of working for a major carrier. She is particularly interested in mentoring the next generation of women pilots.",
    "aviation_path_stage": "training",
    "community_service_summary": "Secretary of school aerospace club; volunteers at local aviation museum teaching children about aviation careers; mentors 3 high school students interested in aviation.",
    "leadership_roles": [
      "Aerospace Club Secretary",
      "Flight Training Mentor",
      "Aviation Museum Youth Programs Volunteer Coordinator"
    ],
    "personal_character_indicators": [
      "persistence",
      "dedication",
      "mentorship",
      "initiative",
      "teamwork",
      "resilience"
    ],
    "alignment_with_wai": "Sarah's commitment to aviation, demonstrated through both personal achievement and commitment to supporting other women in aviation, strongly aligns with WAI's core mission.",
    "unique_strengths": [
      "Early achievement in flight training",
      "Strong academic record",
      "Active in promoting aviation to younger generation",
      "Clear long-term career vision"
    ]
  },
  "scores": {
    "motivation_score": 92,
    "goals_clarity_score": 88,
    "character_service_leadership_score": 85,
    "overall_score": 88
  },
  "score_breakdown": {
    "motivation_score_reasoning": "Sarah demonstrates exceptionally strong and genuine motivation for aviation, backed by concrete actions including private pilot license and ongoing flight training.",
    "goals_clarity_score_reasoning": "Career goals are specific and well-articulated with both short-term (commercial license) and long-term (airline pilot role) objectives.",
    "character_service_leadership_score_reasoning": "Strong leadership through aerospace club role and demonstrated commitment to community service through youth mentoring and museum volunteering.",
    "overall_score_reasoning": "Sarah shows excellent alignment with scholarship criteria with strong motivation, clear goals, demonstrated leadership, and commitment to supporting other women in aviation."
  }
}
```

### Example 2: Career-Changer with Emerging Aviation Interest

```json
{
  "summary": "Michelle recently transitioned to aerospace engineering after a successful career in business, driven by a newfound passion for aviation. While her aviation journey is nascent, she demonstrates strong character through her commitment to adult learning and clear vision for contributing to the aerospace industry. Her leadership experience in her previous career, combined with her service mindset, positions her well for success in aviation.",
  "profile_features": {
    "motivation_summary": "Michelle's interest in aviation developed through volunteer work with an aerospace nonprofit. Inspired by the mission of supporting underrepresented women in STEM, she decided to pursue aerospace engineering as a second career.",
    "career_goals_summary": "Michelle seeks to work in aerospace engineering with a focus on supporting diversity and inclusion initiatives. She hopes to eventually lead programs that encourage women to enter aviation and aerospace fields.",
    "aviation_path_stage": "exploring",
    "community_service_summary": "Volunteer coordinator for women in STEM nonprofit; mentors undergraduate women in engineering; serves on diversity committee for engineering department.",
    "leadership_roles": [
      "Volunteer Coordinator, Women in STEM Nonprofit",
      "Diversity Committee Member, Engineering Department",
      "Peer Mentor for Women in Engineering"
    ],
    "personal_character_indicators": [
      "adaptability",
      "commitment to learning",
      "service-oriented",
      "collaboration",
      "strategic thinking",
      "inclusivity"
    ],
    "alignment_with_wai": "Michelle's commitment to supporting women in aviation and aerospace through both her career transition and volunteer work directly aligns with WAI's advocacy and support mission.",
    "unique_strengths": [
      "Brings diverse professional experience to aerospace field",
      "Strong commitment to diversity and inclusion",
      "Proven leadership in previous career",
      "Mature perspective and intentional career planning"
    ]
  },
  "scores": {
    "motivation_score": 75,
    "goals_clarity_score": 78,
    "character_service_leadership_score": 82,
    "overall_score": 78
  },
  "score_breakdown": {
    "motivation_score_reasoning": "While Michelle's aviation motivation is emerging rather than lifelong, her thoughtful career transition and commitment to the field through action demonstrates genuine interest.",
    "goals_clarity_score_reasoning": "Goals are clear and focused on using aviation/aerospace to support diversity initiatives, with realistic pathways articulated.",
    "character_service_leadership_score_reasoning": "Excellent character indicators with proven leadership from previous career and strong ongoing commitment to service through mentoring and committee work.",
    "overall_score_reasoning": "Michelle shows strong scholarship fit through her character, service orientation, and unique perspective that could benefit the aviation community."
  }
}
```

---

## Academic Agent Schema Examples

### Example 1: High-Performing STEM Student

```json
{
  "summary": "Jessica maintains an excellent 3.85 GPA while pursuing an aerospace engineering degree with a focus on propulsion systems. She has earned multiple academic honors and accolades, and her coursework demonstrates strong preparation for a career in engineering. Her trajectory shows consistent academic growth and deep engagement with her field of study.",
  "profile_features": {
    "current_school_name": "State University of Technology",
    "program": "Aerospace Engineering, Propulsion Systems Track",
    "education_level": "undergraduate",
    "gpa": "3.85",
    "academic_awards": [
      "Dean's List (all semesters)",
      "AIAA Scholarship Award",
      "Women in Engineering Scholarship",
      "Tau Beta Pi Honor Society",
      "Phi Kappa Phi Honor Society"
    ],
    "relevant_courses": [
      "Propulsion Systems Design",
      "Computational Fluid Dynamics",
      "Aircraft Structures and Design",
      "Aerodynamics I and II",
      "Control Systems",
      "Materials Science for Aerospace"
    ],
    "academic_trajectory": "Started with 3.5 GPA freshman year, demonstrating improvement each semester to current 3.85. Progression shows increasing engagement with advanced aerospace coursework.",
    "strengths": [
      "Exceptional grasp of STEM fundamentals",
      "Strong performance in technical courses",
      "Consistent upward trajectory",
      "Effective time management",
      "Deep engagement with aerospace specialization"
    ],
    "areas_for_improvement": []
  },
  "scores": {
    "academic_performance_score": 90,
    "academic_relevance_score": 95,
    "academic_readiness_score": 92,
    "overall_score": 92
  },
  "score_breakdown": {
    "academic_performance_score_reasoning": "3.85 GPA with consistent performance and multiple academic honors demonstrates strong academic capability.",
    "academic_relevance_score_reasoning": "Aerospace engineering major with propulsion focus directly aligns with aviation career. Relevant coursework and specialized track show clear preparation.",
    "academic_readiness_score_reasoning": "Strong STEM foundation, relevant coursework, and academic honors indicate excellent readiness for advanced aviation studies and professional roles."
  }
}
```

### Example 2: Strong Student with Less Traditional Path

```json
{
  "summary": "David is pursuing a degree in mechanical engineering with coursework in aviation applications. While his overall GPA is solid at 3.2, his performance in engineering courses has been consistently strong, particularly in courses directly related to aviation. His trajectory shows increasing focus on aviation-related studies as his degree progressed.",
  "profile_features": {
    "current_school_name": "Central State University",
    "program": "Mechanical Engineering with Aviation Focus",
    "education_level": "undergraduate",
    "gpa": "3.2",
    "academic_awards": [
      "Engineering Department Scholarship",
      "Aeronautics Club Award for Outstanding Contribution"
    ],
    "relevant_courses": [
      "Aerospace Applications of Mechanical Engineering",
      "Aircraft Maintenance and Systems",
      "Flight Mechanics",
      "Turbomachinery Fundamentals",
      "Advanced Dynamics",
      "Systems Engineering"
    ],
    "academic_trajectory": "Overall GPA of 3.2 with notably higher performance in engineering (3.7) and aviation-focused courses (3.8). Shows increasingly strong engagement with aviation specialization in final year.",
    "strengths": [
      "Strong performance in engineering and aviation-focused courses",
      "Practical hands-on learning approach",
      "Demonstrated specialization in aviation despite broader degree",
      "Problem-solving skills applied to real aviation challenges"
    ],
    "areas_for_improvement": [
      "Overall GPA could be higher through improved performance in non-core courses",
      "Limited breadth of general education coursework"
    ]
  },
  "scores": {
    "academic_performance_score": 75,
    "academic_relevance_score": 82,
    "academic_readiness_score": 78,
    "overall_score": 78
  },
  "score_breakdown": {
    "academic_performance_score_reasoning": "3.2 overall GPA is solid, with notably strong performance (3.7-3.8) in engineering and aviation-specific courses indicating capability in relevant subject matter.",
    "academic_relevance_score_reasoning": "While degree is broader mechanical engineering, significant coursework and demonstrated focus on aviation applications shows clear alignment with aviation career.",
    "academic_readiness_score_reasoning": "Strong performance in relevant engineering and aviation courses indicates readiness for advanced technical studies and professional roles, despite broader degree."
  }
}
```

---

## Recommendation Agent Schema Examples

### Example 1: Strong Consensus Endorsement

```json
{
  "summary": "All three recommendation letters provide strong endorsement of the applicant, with consistent themes of technical excellence, dedication to aviation, and outstanding character. The recommenders—spanning academic and professional contexts—paint a cohesive picture of a capable, motivated individual well-suited for aviation careers.",
  "profile_features": {
    "recommendations": [
      {
        "recommender_role": "instructor",
        "relationship_duration": "2 years through multiple aerospace engineering courses",
        "key_strengths_mentioned": [
          "Exceptional technical understanding",
          "Consistent engagement and curiosity",
          "Strong work ethic and dedication",
          "Ability to explain complex concepts clearly"
        ],
        "specific_examples": [
          "Earned top marks in advanced aerodynamics course",
          "Took initiative to help struggling classmates",
          "Completed semester-long propulsion design project with innovative solutions"
        ],
        "potential_concerns": [],
        "overall_tone": "very_positive"
      },
      {
        "recommender_role": "employer",
        "relationship_duration": "1.5 years as intern and part-time employee",
        "key_strengths_mentioned": [
          "Professional and reliable",
          "Quick learner who requires minimal supervision",
          "Strong communication skills",
          "Proactive problem-solving approach"
        ],
        "specific_examples": [
          "Independently identified and implemented efficiency improvements",
          "Trained new interns in department procedures",
          "Successfully led small project team with tight timeline"
        ],
        "potential_concerns": [],
        "overall_tone": "very_positive"
      },
      {
        "recommender_role": "mentor",
        "relationship_duration": "3 years through aerospace club mentoring",
        "key_strengths_mentioned": [
          "Genuine passion for aviation",
          "Supportive and encouraging attitude toward peers",
          "Leadership by example",
          "Commitment to field beyond personal career"
        ],
        "specific_examples": [
          "Mentored 5 younger students, 3 now pursuing aerospace careers",
          "Organized and led first-time flight experience trips for club",
          "Consistently volunteers for club leadership roles"
        ],
        "potential_concerns": [],
        "overall_tone": "very_positive"
      }
    ],
    "aggregate_analysis": {
      "common_themes": [
        "Technical excellence and quick learning",
        "Reliability and strong work ethic",
        "Genuine passion for aviation",
        "Leadership and mentoring ability",
        "Strong communication skills"
      ],
      "strength_consistency": "high",
      "depth_of_support": "deep"
    }
  },
  "scores": {
    "average_support_strength_score": 93,
    "consistency_of_support_score": 94,
    "depth_of_endorsement_score": 91,
    "overall_score": 93
  },
  "score_breakdown": {
    "average_support_strength_score_reasoning": "All three letters provide strong, specific endorsement with concrete examples and consistent themes of excellence.",
    "consistency_of_support_score_reasoning": "Remarkable consistency across academic instructor, employer, and peer mentor regarding technical ability, work ethic, and aviation passion.",
    "depth_of_endorsement_score_reasoning": "Letters demonstrate deep knowledge of applicant across multiple contexts with specific examples and extended relationships."
  }
}
```

### Example 2: Mixed Recommendations with Some Concerns

```json
{
  "summary": "The two recommendation letters provide generally positive support with some nuance. The academic recommender offers strong endorsement of technical capability, while the professional reference highlights growth potential with some initial adjustment period. Both recommend the applicant for further opportunities.",
  "profile_features": {
    "recommendations": [
      {
        "recommender_role": "instructor",
        "relationship_duration": "1 semester in capstone project course",
        "key_strengths_mentioned": [
          "Strong analytical skills",
          "Solid grasp of engineering fundamentals",
          "Completed capstone project successfully",
          "Collaborative team member"
        ],
        "specific_examples": [
          "Led analysis component of team project",
          "Contributed valuable insights to design discussions",
          "Delivered strong final presentation"
        ],
        "potential_concerns": [
          "Sometimes hesitant to voice ideas in large group settings",
          "Limited prior exposure to some aviation-specific software"
        ],
        "overall_tone": "positive"
      },
      {
        "recommender_role": "employer",
        "relationship_duration": "6 months as engineering intern",
        "key_strengths_mentioned": [
          "Willingness to learn",
          "Takes feedback well and implements improvements",
          "Shows increasing confidence and capability",
          "Good team fit and positive attitude"
        ],
        "specific_examples": [
          "Initially struggled with CAD software but became proficient in 2 months",
          "Volunteered for additional training and certification",
          "By end of internship, worked more independently on project tasks"
        ],
        "potential_concerns": [
          "Initial onboarding period was longer than typical",
          "Needed more guidance on industry-standard procedures",
          "Limited professional aviation experience prior to internship"
        ],
        "overall_tone": "positive"
      }
    ],
    "aggregate_analysis": {
      "common_themes": [
        "Solid technical foundation with potential for growth",
        "Positive attitude toward learning and feedback",
        "Good collaborative skills",
        "Need for some development in professional confidence"
      ],
      "strength_consistency": "medium",
      "depth_of_support": "moderate"
    }
  },
  "scores": {
    "average_support_strength_score": 72,
    "consistency_of_support_score": 71,
    "depth_of_endorsement_score": 70,
    "overall_score": 71
  },
  "score_breakdown": {
    "average_support_strength_score_reasoning": "Both recommenders support the applicant with generally positive feedback, though endorsements are measured rather than enthusiastic.",
    "consistency_of_support_score_reasoning": "Both letters mention learning curve and need for skill development, suggesting applicant is capable but requires more support than some candidates.",
    "depth_of_endorsement_score_reasoning": "Relationships are shorter (1 semester, 6 months) which limits depth of knowledge, though both recommenders provide specific observations."
  }
}
```

---

## Academic Performance Agent Schema Examples (Corrected naming)

### Example 1: Strong Student Interested in Professional Certifications

```json
{
  "summary": "Elena has earned her private pilot license and is actively pursuing her instrument rating while maintaining strong academic performance at her university. Her academic transcript demonstrates solid competency in STEM subjects with exceptional performance in aviation-related coursework. She shows strong alignment with aviation career goals and has demonstrated commitment through both academic and practical achievement.",
  "profile_features": {
    "current_school_name": "University of Aviation Studies",
    "program": "Professional Pilot Program",
    "education_level": "undergraduate",
    "gpa": "3.6",
    "academic_awards": [
      "Private Pilot License (current, earned 2023)",
      "Instrument Rating (in progress)",
      "Dean's List for Aviation Students",
      "Flight Training Scholarship"
    ],
    "relevant_courses": [
      "Aviation Meteorology",
      "Air Navigation and Flight Planning",
      "Aircraft Systems and Maintenance",
      "Aviation Regulations and Safety",
      "Commercial Pilot Preparation",
      "Advanced Flight Training"
    ],
    "academic_trajectory": "Consistent 3.6 GPA with increasing specialization in aviation courses. Practical flight training credentials demonstrate applied knowledge and commitment.",
    "strengths": [
      "Practical demonstration of aviation knowledge through pilot certification",
      "Excellent performance in aviation-specific technical courses",
      "Strong commitment to continuous learning in aviation field",
      "Combination of academic and practical preparation"
    ],
    "areas_for_improvement": [
      "Could deepen breadth of STEM coursework beyond aviation focus"
    ]
  },
  "scores": {
    "academic_performance_score": 82,
    "academic_relevance_score": 96,
    "academic_readiness_score": 88,
    "overall_score": 88
  },
  "score_breakdown": {
    "academic_performance_score_reasoning": "3.6 GPA with strong performance in technical courses demonstrates solid academic capability and sustained effort.",
    "academic_relevance_score_reasoning": "Professional pilot program with active flight certifications directly demonstrates commitment and readiness for aviation career.",
    "academic_readiness_score_reasoning": "Combination of relevant coursework and practical pilot training indicates excellent preparation for professional aviation roles and advanced study."
  }
}
```

---

## Social Agent Schema Examples

### Example 1: Strong Professional and Social Presence

```json
{
  "summary": "The applicant demonstrates a robust social media presence across multiple platforms with strong emphasis on professional networking and aviation content sharing. LinkedIn profile shows active engagement with the aerospace industry, while Instagram reflects both professional development activities and personal aviation interests.",
  "profile_features": {
    "platforms_found": {
      "facebook": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No Facebook link or reference found in application materials"
      },
      "instagram": {
        "present": true,
        "link": "https://instagram.com/sarah.aviation.journey",
        "handle": "@sarah.aviation.journey",
        "evidence": "Instagram handle listed in resume under professional profiles; posts include flight training updates and aviation events"
      },
      "tiktok": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No TikTok presence mentioned or referenced in application"
      },
      "linkedin": {
        "present": true,
        "link": "https://linkedin.com/in/sarahpilotstudent",
        "handle": "sarahpilotstudent",
        "evidence": "LinkedIn URL prominently listed in resume contact section; profile shows 500+ connections and active engagement with aerospace industry content"
      }
    },
    "total_platforms": 2,
    "has_professional_presence": true,
    "notes": "Applicant maintains professional presence on Instagram with aviation-focused content. Strong LinkedIn presence with active industry engagement demonstrates serious commitment to aviation career development."
  },
  "scores": {
    "social_presence_score": 70,
    "professional_presence_score": 88,
    "overall_score": 79
  },
  "score_breakdown": {
    "social_presence_score_reasoning": "Active presence on 2 of 4 major platforms. Instagram activity shows sustained engagement with aviation-related content.",
    "professional_presence_score_reasoning": "Strong LinkedIn presence with substantial network and regular industry engagement. LinkedIn is primary professional platform and shows serious career focus.",
    "overall_score_reasoning": "Solid professional social media presence, particularly on LinkedIn, indicating active professional networking and genuine industry engagement."
  }
}
```

### Example 2: Minimal Social Media Presence

```json
{
  "summary": "The applicant has minimal presence on social media platforms. While no social media profiles were identified in application materials, this does not necessarily reflect lack of engagement, as not all applicants maintain active social media presence.",
  "profile_features": {
    "platforms_found": {
      "facebook": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No Facebook profile or reference mentioned in application materials"
      },
      "instagram": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No Instagram handle or profile link provided"
      },
      "tiktok": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No TikTok presence indicated"
      },
      "linkedin": {
        "present": false,
        "link": null,
        "handle": null,
        "evidence": "No LinkedIn profile referenced in resume or application materials"
      }
    },
    "total_platforms": 0,
    "has_professional_presence": false,
    "notes": "Applicant does not maintain visible social media presence. This may reflect preference for privacy or limited engagement with social media. Does not necessarily indicate lack of professional networking; applicant may network through other channels."
  },
  "scores": {
    "social_presence_score": 0,
    "professional_presence_score": 0,
    "overall_score": 15
  },
  "score_breakdown": {
    "social_presence_score_reasoning": "No social media platforms identified. Without social media profiles, baseline score reflects absence of measured presence.",
    "professional_presence_score_reasoning": "No LinkedIn or other professional social media presence identified. Applicant may utilize other professional networking methods not captured in application materials.",
    "overall_score_reasoning": "Limited social media presence may indicate preference for privacy or alternative networking approaches. Score reflects verifiable absence rather than indication of professional capability."
  }
}
```

---

## Application Agent Schema Examples

### Example 1: Complete Application

```json
{
  "profile": {
    "wai_membership_number": "WAI-2024-45321",
    "wai_application_number": "DELANEY-2026-12345",
    "first_name": "Jennifer",
    "middle_name": "Marie",
    "last_name": "Martinez",
    "email": "j.martinez@email.com",
    "membership_since": "2023-06-15",
    "membership_expiration": "2025-06-14",
    "home_address": {
      "country": "United States",
      "address_1": "1234 Aviation Lane",
      "address_2": "Apt 5B",
      "city": "Phoenix",
      "state_province": "Arizona",
      "zip_postal_code": "85001",
      "home_phone": "(602) 555-0123",
      "work_phone": "(602) 555-0124"
    },
    "school_information": {
      "country": "United States",
      "school_name": "Arizona State University",
      "address_1": "101 University Way",
      "address_2": null,
      "city": "Tempe",
      "state_province": "Arizona",
      "zip_postal_code": "85281"
    },
    "completeness": {
      "has_resume": true,
      "has_essay": true,
      "num_recommendation_letters": 3,
      "has_medical_certificate": true,
      "has_logbook": true,
      "num_attachments": 6
    }
  },
  "summary": "Jennifer Martinez is a complete applicant for the Delaney Wings Scholarship with all required materials submitted. Current WAI member since 2023, she provides comprehensive contact information and clear school affiliation with Arizona State University. Her submission includes resume, essay, three strong recommendation letters, medical certificate, and flight logbook, indicating serious engagement with aviation and thorough preparation.",
  "scores": {
    "overall_score": 95,
    "completeness_score": 100,
    "score_breakdown": {
      "profile_information": "100 - Complete name, email, and contact numbers provided",
      "contact_information": "100 - Full home address with both phone numbers present",
      "school_information": "100 - School name, city, state, and zip code all provided",
      "supporting_documents": "100 - All required documents submitted (resume, essay, 3 recommendations, medical cert, logbook)"
    },
    "missing_items": []
  }
}
```

### Example 2: Partial Application with Missing Items

```json
{
  "profile": {
    "wai_membership_number": null,
    "wai_application_number": "DELANEY-2026-12346",
    "first_name": "Michael",
    "middle_name": null,
    "last_name": "Chen",
    "email": "mchen.aviation@email.com",
    "membership_since": null,
    "membership_expiration": null,
    "home_address": {
      "country": "United States",
      "address_1": "567 Mountain Road",
      "address_2": null,
      "city": "Denver",
      "state_province": "Colorado",
      "zip_postal_code": "80202",
      "home_phone": null,
      "work_phone": "(303) 555-9876"
    },
    "school_information": {
      "country": "United States",
      "school_name": "University of Colorado Boulder",
      "address_1": null,
      "address_2": null,
      "city": "Boulder",
      "state_province": "Colorado",
      "zip_postal_code": null
    },
    "completeness": {
      "has_resume": true,
      "has_essay": true,
      "num_recommendation_letters": 2,
      "has_medical_certificate": false,
      "has_logbook": false,
      "num_attachments": 3
    }
  },
  "summary": "Michael Chen submitted an incomplete application for the Delaney Wings Scholarship. While he provided basic contact and school information, several items are missing. He is not currently a WAI member and did not provide complete school address information. His supporting documents are limited: 2 recommendation letters and no medical certificate or flight logbook.",
  "scores": {
    "overall_score": 62,
    "completeness_score": 58,
    "score_breakdown": {
      "profile_information": "67 - Name and email present but no WAI membership number or middle name",
      "contact_information": "75 - Home address present but missing home phone number; only work phone provided",
      "school_information": "67 - School name and city provided but missing street address and zip code",
      "supporting_documents": "50 - Missing medical certificate and flight logbook; only 2 recommendation letters instead of 3"
    },
    "missing_items": [
      "WAI membership number",
      "Medical certificate",
      "Flight logbook",
      "Complete school address (street address and zip code)",
      "Home phone number",
      "Third recommendation letter"
    ]
  }
}
```

---

## Using These Examples in Agent Prompts

To integrate these examples into agent prompts, add them before the closing instruction. For example:

```python
prompt = f"""[Agent description and task instructions...]

Example of expected output:

{example_json}

[Rest of prompt with structure description...]

Return ONLY valid JSON, no additional text or markdown formatting."""
```

### Benefits:
1. **Improves JSON output quality** - Concrete examples help LLMs generate properly formatted responses
2. **Shows desired level of detail** - Examples demonstrate expected depth and specificity
3. **Reduces parsing errors** - Well-formatted examples reduce malformed JSON responses
4. **Clarifies ambiguous requirements** - Examples clarify what should and shouldn't be included

### Notes:
- Use appropriate example based on expected input quality
- Good example: applicant with all materials (Example 1)
- Good counterexample: applicant with missing materials (Example 2)
- Examples help LLMs understand context-dependent requirements (e.g., different tones for different scenarios)
