# Jobsy Development Roadmap
**16-Week Implementation Plan | April - July 2026**

---

## Overview

This roadmap outlines a 16-week journey from concept to market-ready product. The plan is divided into two major phases:

- **Phase 1 (Weeks 1-8): MVP Development** - Core features needed for private beta
- **Phase 2 (Weeks 9-16): Enhancement & Scale** - Advanced features and public launch prep

**Team Structure (Assumed):**
- 1 Backend Engineer
- 1 Full-Stack Engineer  
- 1 Product Manager (You)
- 1 QA/DevOps (Part-time)

**Development Philosophy:**
- Ship weekly increments
- User feedback after Week 4
- Bias toward done over perfect
- Technical debt is okay in MVP if documented

---

## Phase 1: MVP Development (Weeks 1-8)

### **Week 1-2: Foundation & Infrastructure**

#### **Week 1: Project Setup & Core Infrastructure**

**Backend Setup:**
- [x] Initialize FastAPI project structure
- [x] Configure PostgreSQL database with SQLAlchemy async
- [x] Set up Docker Compose for local development
- [x] Implement basic authentication (JWT)
- [x] Create database migrations (Alembic)
- [x] Set up logging & error tracking (Sentry)

**WhatsApp Integration:**
- [ ] Apply for WhatsApp Business API access (Meta)
  - Business verification
  - Use case documentation
  - Expected approval: 5-7 days
- [ ] Set up webhook endpoint for incoming messages
- [ ] Implement message sending (text, buttons, media)
- [ ] Test with sandbox account

**Environment Setup:**
- [ ] AWS account setup (EC2, RDS, S3)
- [ ] Configure staging environment
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Domain registration & SSL certificates

**Database Schema:**
```sql
-- Core tables for Week 1
CREATE TABLE users (
    id UUID PRIMARY KEY,
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    whatsapp_name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    subscription_tier VARCHAR(20) DEFAULT 'free',
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE user_profiles (
    user_id UUID PRIMARY KEY REFERENCES users(id),
    current_role VARCHAR(100),
    target_role VARCHAR(100),
    years_of_experience INT,
    expected_salary_min INT,
    expected_salary_max INT,
    preferred_locations JSONB,
    remote_ok BOOLEAN,
    skills JSONB,
    resume_url VARCHAR(500)
);

CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    messages JSONB,
    context JSONB,
    last_message_at TIMESTAMP DEFAULT NOW()
);
```

**Deliverables:**
- ✅ Working FastAPI server deployed to staging
- ✅ Database with core tables
- ✅ WhatsApp webhook receiving test messages
- ✅ CI/CD pipeline deploying on push

**Blockers & Risks:**
- ⚠️ WhatsApp API approval may take 7-10 days (mitigate: use sandbox for dev)
- ⚠️ AWS costs estimation needed

---

#### **Week 2: Conversation Engine (Claude Integration)**

**AI Integration:**
- [ ] Set up Claude API client
- [ ] Implement conversation state management
- [ ] Build intent detection system
- [ ] Create prompt templates for common flows
- [ ] Test conversation quality with 10 sample scenarios

**Conversation Flows to Implement:**
1. **Onboarding Flow**
   - Detect first-time user
   - Ask qualifying questions (role, location, salary)
   - Store context in database
   - Transition to resume upload

2. **Help Flow**
   - List available commands
   - Explain features

3. **Job Discovery Flow** (basic placeholder)
   - Acknowledge request
   - Return mock jobs (hardcoded for now)

**Sample Prompt Structure:**
```python
SYSTEM_PROMPT = """
You are Jobsy, a job search assistant for India.

User Context:
{user_context}

Available Actions:
- trigger_job_search()
- trigger_resume_upload()
- show_application_status()

Conversation History:
{history}

User: {message}

Respond conversationally and execute relevant actions.
"""
```

**Testing:**
- Unit tests for intent detection
- End-to-end test: Full onboarding conversation
- Latency test: Claude API response time (<2s target)

**Deliverables:**
- ✅ Working conversation engine
- ✅ Onboarding flow functional
- ✅ Conversation state persisted in DB
- ✅ Basic error handling for API failures

---

### **Week 3-4: Resume Handling & Job Scraping**

#### **Week 3: Resume Upload & Parsing**

**Resume Storage:**
- [ ] Implement S3 upload endpoint
- [ ] Create signed URLs for secure downloads
- [ ] File validation (PDF/DOCX only, <5MB)
- [ ] Virus scanning (ClamAV integration)

**Resume Parsing:**
- [ ] Integrate open-source parser (pyresparser or custom)
- [ ] Extract: name, email, phone, education, experience, skills
- [ ] Store parsed data in user_profiles table
- [ ] Handle parsing failures gracefully

**ATS Scoring (Basic Version):**
- [ ] Implement scoring algorithm
  - Formatting check (20 pts)
  - Contact info visibility (10 pts)
  - Keywords presence (30 pts)
  - Experience format (20 pts)
  - Skills section (20 pts)
- [ ] Return score + top 3 issues to user
- [ ] Store score in database

**User Flow:**
```
User uploads resume
  → Upload to S3
  → Parse content
  → Calculate ATS score
  → Return score + feedback via WhatsApp
  → Update user_profile with parsed data
```

**Database Updates:**
```sql
ALTER TABLE user_profiles ADD COLUMN ats_score INT;
ALTER TABLE user_profiles ADD COLUMN resume_parsed_at TIMESTAMP;
```

**Deliverables:**
- ✅ Resume upload working via WhatsApp
- ✅ Parsing extracts key fields with 80%+ accuracy
- ✅ ATS score calculation implemented
- ✅ User receives score + feedback

---

#### **Week 4: Job Scraping (Naukri & LinkedIn)**

**Scraper Architecture:**
- [ ] Create base scraper class
- [ ] Implement Naukri scraper
  - Search by keywords, location
  - Extract: title, company, location, salary, URL, description
  - Handle pagination
  - Respect rate limits (max 1 request/second)
- [ ] Implement LinkedIn scraper (via Playwright)
  - Login with test account
  - Search jobs
  - Extract job details
  - Handle anti-bot measures

**Job Storage:**
```sql
CREATE TABLE jobs (
    id UUID PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    external_id VARCHAR(100) UNIQUE,
    title VARCHAR(200),
    company VARCHAR(200),
    location VARCHAR(100),
    remote BOOLEAN,
    salary_min INT,
    salary_max INT,
    description TEXT,
    requirements JSONB,
    posted_at TIMESTAMP,
    apply_url VARCHAR(500),
    ats_type VARCHAR(50),
    scraped_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_jobs_title ON jobs(title);
CREATE INDEX idx_jobs_location ON jobs(location);
CREATE INDEX idx_jobs_scraped_at ON jobs(scraped_at);
```

**Scheduled Jobs:**
- [ ] Set up APScheduler
- [ ] Schedule Naukri scraper (every 4 hours)
- [ ] Schedule LinkedIn scraper (every 6 hours)
- [ ] Implement deduplication logic

**Testing:**
- Scrape 100 jobs from Naukri
- Verify data quality (all fields populated)
- Test rate limiting & error handling

**Deliverables:**
- ✅ Naukri scraper collecting 500+ jobs/day
- ✅ LinkedIn scraper collecting 200+ jobs/day
- ✅ Jobs stored in database
- ✅ Scheduled jobs running reliably

**End of Week 4 Milestone:**
🎯 **Internal Demo #1**
- Show end-to-end flow: User onboards → Uploads resume → Receives jobs
- Test with 5 internal users
- Collect feedback on conversation quality

---

### **Week 5-6: Job Matching & Auto-Apply**

#### **Week 5: Job Matching Engine**

**Matching Algorithm:**
- [ ] Implement scoring function (see PRD Section 7.2)
- [ ] Create match_jobs_for_user() function
- [ ] Filter jobs by score threshold (>=60)
- [ ] Sort by relevance + recency

**Daily Job Digest:**
- [ ] Create scheduled task (9 AM daily)
- [ ] For each active user:
  - Find top 10 new matches
  - Send WhatsApp message with job cards
  - Include reaction buttons (✅ ❌ 🔖)
- [ ] Handle user reactions
  - ✅ → Queue for auto-apply
  - ❌ → Mark as not interested
  - 🔖 → Save for later

**User Preferences:**
```sql
CREATE TABLE user_job_preferences (
    user_id UUID REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    preference VARCHAR(20), -- 'apply', 'skip', 'save'
    created_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (user_id, job_id)
);
```

**Testing:**
- Create 10 test users with different profiles
- Verify each gets relevant matches
- Check for false positives (irrelevant jobs shown)

**Deliverables:**
- ✅ Matching algorithm returns relevant jobs
- ✅ Daily digest sent successfully
- ✅ User reactions stored and processed

---

#### **Week 6: Auto-Apply (Phase 1 - Greenhouse & Lever)**

**Playwright Setup:**
- [ ] Install Playwright with browser binaries
- [ ] Create browser pool (max 5 concurrent instances)
- [ ] Implement stealth plugins (avoid detection)

**Greenhouse Auto-Apply:**
- [ ] Navigate to application URL
- [ ] Fill form fields:
  - Name, Email, Phone
  - Resume upload
  - Cover letter (optional)
- [ ] Answer screening questions (use Claude)
- [ ] Submit application
- [ ] Capture confirmation or error

**Lever Auto-Apply:**
- [ ] Similar flow as Greenhouse
- [ ] Handle multi-step forms
- [ ] Deal with custom fields

**Application Tracking:**
```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    job_id UUID REFERENCES jobs(id),
    status VARCHAR(50) DEFAULT 'applied',
    auto_applied BOOLEAN DEFAULT true,
    applied_at TIMESTAMP DEFAULT NOW(),
    error_message TEXT,
    confirmation_id VARCHAR(100)
);

CREATE INDEX idx_applications_user ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
```

**Error Handling:**
- Captcha detected → Notify user
- Form field not found → Log error, notify user
- Timeout → Retry once, then fail

**Rate Limiting:**
- Max 50 applications/day per user
- Max 10/hour
- 30-second delay between applications

**Testing:**
- Test with 10 real job applications
- Verify success rate >85%
- Check for detection/blocking

**Deliverables:**
- ✅ Auto-apply working for Greenhouse
- ✅ Auto-apply working for Lever
- ✅ Applications tracked in database
- ✅ User notified of success/failure

---

### **Week 7: Application Tracking & Notifications**

**Status Dashboard:**
- [ ] Implement "status" command
- [ ] Query applications for user
- [ ] Group by status (applied, under review, interview, rejected, offer)
- [ ] Format response as WhatsApp message

**Notification System:**
- [ ] Email parsing (optional - if user grants Gmail access)
  - Detect "Application received" emails
  - Detect "Interview invitation" emails
  - Update application status
- [ ] Push notifications via WhatsApp
  - "Your application to [Company] was viewed"
  - "Interview invite from [Company]"

**Recruiter View Detection (Basic):**
- [ ] Scrape LinkedIn "Who's viewed your profile"
- [ ] Match viewers to applications
- [ ] Notify user if recruiter viewed profile after application

**Database Updates:**
```sql
ALTER TABLE applications ADD COLUMN recruiter_viewed BOOLEAN DEFAULT false;
ALTER TABLE applications ADD COLUMN last_updated TIMESTAMP;

CREATE TABLE application_events (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    event_type VARCHAR(50), -- 'viewed', 'interview_invite', 'rejected'
    event_data JSONB,
    occurred_at TIMESTAMP DEFAULT NOW()
);
```

**Deliverables:**
- ✅ Status dashboard functional
- ✅ Notifications sent for key events
- ✅ Application history tracked

---

### **Week 8: MVP Polish & Private Beta Launch**

**Week 8 Focus: Bug Fixes, Testing, & Documentation**

**Bug Bash:**
- [ ] Fix top 10 bugs from internal testing
- [ ] Improve error messages
- [ ] Add loading states ("Applying to jobs, please wait...")
- [ ] Handle edge cases (empty resume, invalid phone number)

**Performance Optimization:**
- [ ] Optimize database queries (add missing indexes)
- [ ] Reduce Claude API latency (batch requests where possible)
- [ ] Speed up resume parsing (<5 seconds)

**User Onboarding Improvements:**
- [ ] Simplify onboarding questions (reduce from 7 to 5)
- [ ] Add sample conversation in welcome message
- [ ] Create "Quick Start Guide" (sent after signup)

**Documentation:**
- [ ] API documentation (for internal use)
- [ ] Deployment runbook
- [ ] Troubleshooting guide
- [ ] User FAQ document

**Private Beta Preparation:**
- [ ] Recruit 50 beta users (from network)
- [ ] Create beta signup form
- [ ] Set up feedback collection (Typeform survey)
- [ ] Prepare launch email/WhatsApp message

**Launch Checklist:**
- [ ] All core flows tested end-to-end
- [ ] Staging environment stable
- [ ] Production environment configured
- [ ] Monitoring & alerts set up
- [ ] Customer support channel ready (WhatsApp group for beta users)

**Deliverables:**
- ✅ MVP feature-complete
- ✅ 50 beta users onboarded
- ✅ Zero critical bugs
- ✅ Average conversation latency <3 seconds

---

## **End of Week 8 Milestone: MVP LAUNCH** 🚀

**Success Criteria:**
- 50 beta users onboarded
- 70% complete onboarding (upload resume)
- 500+ jobs scraped and matched
- 200+ applications submitted via auto-apply
- 4.0+ satisfaction score from beta users
- <5% auto-apply failure rate

**Go/No-Go Decision:**
If success criteria met → Proceed to Phase 2 (public launch prep)
If not met → Extend MVP phase by 2 weeks, fix critical gaps

---

## Phase 2: Enhancement & Scale (Weeks 9-16)

### **Week 9-10: Resume Optimization & Advanced Features**

#### **Week 9: ATS Resume Optimizer**

**Optimization Engine:**
- [ ] Build resume rewriting logic (Claude-powered)
- [ ] Extract keywords from job descriptions
- [ ] Identify missing skills from user's experience
- [ ] Rephrase bullet points for impact (add metrics)
- [ ] Generate optimized resume (DOCX format)

**Optimization Flow:**
```
User triggers "optimize resume"
  → Fetch user's current resume
  → Analyze against target job descriptions
  → Generate suggestions (keyword additions, rephrasing)
  → User reviews changes
  → Generate new resume file
  → Upload to S3
  → Update user_profile.resume_url
```

**Resume Templates:**
- [ ] Create 3 ATS-friendly templates
  - Minimal (single column, clean)
  - Modern (two-column, subtle colors)
  - Technical (emphasis on projects/skills)
- [ ] Let user choose template
- [ ] Apply template to resume content

**Testing:**
- Test with 20 real resumes
- Measure ATS score improvement (target: +20 points avg)
- User feedback on optimization quality

**Deliverables:**
- ✅ Optimization engine working
- ✅ Average ATS score improves by 20+ points
- ✅ User can download optimized resume

---

#### **Week 10: Multi-ATS Support**

**Expand Auto-Apply Coverage:**
- [ ] Add Workday support
  - Handle multi-page forms
  - Deal with custom dropdowns
  - Navigate complex flows
- [ ] Add SmartRecruiters support
- [ ] Add Naukri Quick Apply support
- [ ] Add LinkedIn Easy Apply support

**ATS Detection Logic:**
- [ ] Identify ATS from job URL
- [ ] Route to appropriate automation script
- [ ] Fallback to generic form-filling for unknown ATS

**Reliability Improvements:**
- [ ] Retry failed applications (max 2 retries)
- [ ] Better error logging (screenshot on failure)
- [ ] Alert system for repeated failures on same ATS

**Updated ATS Support Matrix:**
| ATS | Status |
|-----|--------|
| Greenhouse | ✅ |
| Lever | ✅ |
| Workday | ✅ (Week 10) |
| SmartRecruiters | ✅ (Week 10) |
| Naukri QA | ✅ (Week 10) |
| LinkedIn EA | ✅ (Week 10) |

**Deliverables:**
- ✅ 6 ATS platforms supported
- ✅ Auto-apply success rate >88%
- ✅ Better error reporting

---

### **Week 11-12: Recruiter Outreach & Analytics**

#### **Week 11: LinkedIn Recruiter Outreach**

**Recruiter Discovery:**
- [ ] Scrape LinkedIn for recruiters at target companies
- [ ] Filter by title ("Recruiter", "Talent Acquisition", "HR")
- [ ] Extract profile URL, name, company
- [ ] Store in database

**Message Generation:**
- [ ] Create personalized message template (Claude)
- [ ] Insert user's background
- [ ] Reference specific job opening (if available)
- [ ] Keep message under 300 characters

**Automation:**
- [ ] Send connection request via Playwright
- [ ] Add personalized note
- [ ] Track sent messages (avoid duplicates)
- [ ] Monitor acceptance rate

**Database:**
```sql
CREATE TABLE recruiter_outreach (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    recruiter_name VARCHAR(100),
    recruiter_profile_url VARCHAR(500),
    company VARCHAR(100),
    message_sent TEXT,
    sent_at TIMESTAMP,
    connection_accepted BOOLEAN,
    responded BOOLEAN
);
```

**Rate Limiting:**
- Max 10 connection requests/day per user
- Track daily quota in user_profiles

**Deliverables:**
- ✅ Recruiter outreach working
- ✅ 10 messages/day limit enforced
- ✅ 30%+ connection acceptance rate

---

#### **Week 12: Application Analytics Dashboard**

**Metrics to Track:**
- Total applications sent
- Applications by status (applied, interview, rejected, offer)
- Response rate (% of applications that get response)
- Average time to response
- Top performing companies (highest callback rate)
- Top performing job titles

**Dashboard Implementation:**
- [ ] Create analytics queries
- [ ] Build WhatsApp-friendly summary
- [ ] Add "analytics" command
- [ ] Show weekly/monthly breakdown

**Example Analytics Output:**
```
📊 Your Job Hunt Analytics (Last 30 Days)

Applications Sent: 127
Response Rate: 18% (23 callbacks)
Interviews Scheduled: 5

Top Companies:
1. Flipkart - 3 callbacks (60% rate)
2. Razorpay - 2 callbacks (40% rate)
3. Swiggy - 1 callback (20% rate)

Best Job Titles:
1. Senior SDE - 12 applications, 4 callbacks (33%)
2. Backend Engineer - 18 applications, 5 callbacks (28%)

Next Steps:
- Focus more on "Senior SDE" roles (higher callback rate)
- Follow up with Flipkart (interview scheduled)
```

**Deliverables:**
- ✅ Analytics dashboard functional
- ✅ Insights actionable for users
- ✅ Weekly analytics digest sent automatically

---

### **Week 13: Interview Prep & Salary Intelligence**

**Mock Interview (Voice-based):**
- [ ] Integrate WhatsApp voice message handling
- [ ] Store common interview questions
- [ ] Send voice question to user
- [ ] User responds with voice
- [ ] Transcribe response (Whisper API or similar)
- [ ] Analyze with Claude (provide feedback)

**Interview Question Bank:**
- [ ] Curate 50 common questions by category
  - Behavioral (20)
  - Technical (20)
  - Company-specific (10)
- [ ] Store in database
- [ ] Randomize questions for variety

**Company Research Brief:**
- [ ] Scrape company data (website, news, Glassdoor)
- [ ] Generate 1-page brief:
  - Company overview
  - Recent news/funding
  - Culture insights
  - Interview process notes
- [ ] Send as PDF via WhatsApp

**Salary Benchmarking:**
- [ ] Scrape salary data from Glassdoor, AmbitionBox
- [ ] Store in database by company, role, experience
- [ ] Create "salary" command
- [ ] Show percentile ranges (25th, 50th, 75th)

**Database:**
```sql
CREATE TABLE salary_data (
    id UUID PRIMARY KEY,
    company VARCHAR(100),
    role VARCHAR(100),
    experience_min INT,
    experience_max INT,
    salary_min INT,
    salary_max INT,
    location VARCHAR(100),
    source VARCHAR(50),
    updated_at TIMESTAMP
);
```

**Deliverables:**
- ✅ Mock interview working (voice-based)
- ✅ Company research briefs generated
- ✅ Salary data for top 50 companies

---

### **Week 14: Monetization & Billing**

**Pricing Tiers Implementation:**
- [ ] Define tier limits in code
  - Free: 10 applications/month
  - Basic (₹999): 100 applications/month
  - Premium (₹2999): Unlimited applications
- [ ] Implement usage tracking
- [ ] Show usage in "status" command

**Payment Integration:**
- [ ] Integrate Razorpay payment gateway
- [ ] Create subscription checkout flow
  - User sends "upgrade"
  - Receive Razorpay payment link
  - User completes payment
  - Webhook updates subscription_tier
- [ ] Handle subscription renewals
- [ ] Send payment reminders (3 days before expiry)

**Billing Database:**
```sql
CREATE TABLE subscriptions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    tier VARCHAR(20),
    started_at TIMESTAMP,
    expires_at TIMESTAMP,
    razorpay_subscription_id VARCHAR(100),
    status VARCHAR(20) -- active, cancelled, expired
);

CREATE TABLE payments (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    amount INT,
    currency VARCHAR(3) DEFAULT 'INR',
    razorpay_payment_id VARCHAR(100),
    status VARCHAR(20),
    paid_at TIMESTAMP
);
```

**Free → Paid Conversion Flow:**
```
User hits free tier limit (10 applications)
  → Send message: "You've used all 10 free applications this month! 
     Upgrade to Basic (₹999/mo) for 100 more applications."
  → Provide upgrade link
  → User clicks, completes payment
  → Subscription activated
  → User can now apply to more jobs
```

**Testing:**
- Test payment flow end-to-end
- Verify subscription upgrades work
- Test renewal logic
- Handle failed payments gracefully

**Deliverables:**
- ✅ Payment integration working
- ✅ Tier limits enforced
- ✅ Upgrade flow smooth
- ✅ First paying customer!

---

### **Week 15: Public Launch Preparation**

**Marketing Assets:**
- [ ] Create landing page (Next.js or simple HTML)
  - Hero: "Land your next job while you sleep"
  - Features: Job automation, resume optimization, AI assistant
  - Pricing table
  - Signup CTA
- [ ] Record demo video (3 minutes)
  - Show onboarding
  - Show job matching
  - Show auto-apply in action
- [ ] Write launch blog post ("How I automated my job hunt")
- [ ] Design social media assets (Instagram, LinkedIn posts)

**Content Marketing:**
- [ ] Create SEO-optimized guides:
  - "ATS Resume Guide for India 2026"
  - "How to get more interview callbacks"
  - "Job hunting automation: Complete guide"
- [ ] Publish on Medium, LinkedIn, personal blog

**Community Building:**
- [ ] Create WhatsApp Community (for user discussions)
- [ ] Set up Discord server (optional)
- [ ] Launch referral program
  - Give 1 month Premium for every 3 referrals
  - Track via unique referral codes

**PR Outreach:**
- [ ] Draft press release
- [ ] Reach out to YourStory, Inc42, TechCrunch India
- [ ] Pitch story: "India's first WhatsApp job automation platform"

**Influencer Partnerships:**
- [ ] Identify 5 LinkedIn influencers in job hunting space
- [ ] Offer free Premium access in exchange for review/mention
- [ ] Track conversions from influencer links

**Deliverables:**
- ✅ Landing page live
- ✅ Demo video recorded
- ✅ Blog post published
- ✅ Outreach to 3 publications

---

### **Week 16: Public Launch & Growth**

**Launch Week Activities:**

**Monday (Launch Day):**
- [ ] Publish landing page
- [ ] Post launch announcement on LinkedIn, Twitter, WhatsApp Status
- [ ] Send email to beta users asking for testimonials/referrals
- [ ] Submit to Product Hunt

**Tuesday:**
- [ ] Publish blog post on Medium
- [ ] Share in relevant Facebook/LinkedIn groups
- [ ] Monitor signups and onboarding completion rate

**Wednesday:**
- [ ] Engage with Product Hunt comments
- [ ] Respond to social media mentions
- [ ] Fix any critical bugs reported

**Thursday:**
- [ ] Send personalized LinkedIn messages to target users
- [ ] Post demo video on YouTube
- [ ] Start paid ad campaigns (Google Search, Facebook)

**Friday:**
- [ ] Publish week 1 metrics (signups, applications sent, etc.)
- [ ] Collect user testimonials
- [ ] Plan week 2 growth experiments

**Growth Experiments:**
1. **Referral Program Test:**
   - Variant A: 1 month Premium for 3 referrals
   - Variant B: 2 months Premium for 5 referrals
   - Track which drives more invites

2. **Onboarding Funnel Optimization:**
   - A/B test: 5 questions vs. 3 questions
   - Track completion rate

3. **Paid Ad Testing:**
   - Google Search: "job automation India"
   - Facebook: Target 22-32, interests = job search
   - Budget: ₹10K/week
   - Target CAC: <₹500

**Success Metrics (Week 16):**
- 1,000+ signups
- 700+ users completed onboarding (70%)
- 5,000+ job applications sent
- 50+ paying customers (5% conversion)
- ₹50K MRR
- 4.5+ app rating (if mobile app launched)

**Deliverables:**
- ✅ Successful public launch
- ✅ 1,000+ users acquired
- ✅ Product Hunt featured
- ✅ ₹50K MRR

---

## Post-Launch Roadmap (Weeks 17-24)

**Week 17-18: Mobile App (iOS/Android)**
- React Native app development
- Sync with WhatsApp backend
- Push notifications
- App Store & Play Store submission

**Week 19-20: Advanced Automation**
- LinkedIn profile optimization
- Auto-respond to recruiter messages
- Follow-up email automation

**Week 21-22: B2B Talent Pool**
- Recruiter dashboard (web app)
- Candidate search & filtering
- Candidate unlock & contact
- Billing for B2B customers

**Week 23-24: Community & Scale**
- Job hunting tips community
- Success stories showcase
- Webinars on interview prep
- Scale to 10,000+ users

---

## Resource Allocation

### **Effort Distribution (Person-Weeks)**

| Module | Backend | Frontend | Product | QA/DevOps | Total |
|--------|---------|----------|---------|-----------|-------|
| Infrastructure | 1.5 | 0.5 | 0.5 | 0.5 | 3 |
| Conversation Engine | 1.0 | 0.0 | 1.0 | 0.5 | 2.5 |
| Resume Handling | 1.5 | 0.0 | 0.5 | 0.5 | 2.5 |
| Job Scraping | 2.0 | 0.0 | 0.5 | 0.5 | 3 |
| Job Matching | 1.0 | 0.0 | 0.5 | 0.5 | 2 |
| Auto-Apply | 3.0 | 0.0 | 0.5 | 1.0 | 4.5 |
| Tracking & Notifs | 1.0 | 0.5 | 0.5 | 0.5 | 2.5 |
| MVP Polish | 0.5 | 0.5 | 1.0 | 1.0 | 3 |
| Resume Optimizer | 1.5 | 0.0 | 0.5 | 0.5 | 2.5 |
| Multi-ATS Support | 2.0 | 0.0 | 0.5 | 0.5 | 3 |
| Recruiter Outreach | 1.5 | 0.0 | 0.5 | 0.5 | 2.5 |
| Analytics | 1.0 | 0.5 | 0.5 | 0.5 | 2.5 |
| Interview Prep | 1.5 | 0.0 | 0.5 | 0.5 | 2.5 |
| Monetization | 1.0 | 1.0 | 1.0 | 0.5 | 3.5 |
| Launch Prep | 0.5 | 1.5 | 2.0 | 0.5 | 4.5 |
| **Total** | **20** | **4.5** | **10.5** | **9** | **44** |

**Total Team Effort:** 44 person-weeks over 16 weeks = ~2.75 FTE

---

## Risk Mitigation

### **Critical Risks & Mitigation Plans**

#### **Risk 1: WhatsApp API Approval Delay**
- **Likelihood:** Medium
- **Impact:** High (blocks launch)
- **Mitigation:**
  - Apply early (Week 1)
  - Have detailed use case documentation ready
  - Fallback: SMS-based beta launch via Twilio

#### **Risk 2: Auto-Apply Detection/Blocking**
- **Likelihood:** High
- **Impact:** High (core feature fails)
- **Mitigation:**
  - Implement anti-detection (Week 6)
  - Rate limiting & randomization
  - Fallback: Semi-automated (user completes captchas)
  - Manual application option always available

#### **Risk 3: Low Free → Paid Conversion**
- **Likelihood:** Medium
- **Impact:** High (revenue targets missed)
- **Mitigation:**
  - Strong freemium hook (10 applications/month creates urgency)
  - Demonstrate ROI in free tier (show applications sent)
  - A/B test pricing (₹499, ₹999, ₹1499)
  - Offer limited-time discount for early adopters

#### **Risk 4: Job Market Downturn**
- **Likelihood:** Low (but possible)
- **Impact:** High (demand drops)
- **Mitigation:**
  - Position as efficiency tool (even in downturns, automation saves time)
  - Pivot messaging: "Stand out in a tough market"
  - Diversify revenue (B2B recruiter access)

#### **Risk 5: Technical Debt Accumulation**
- **Likelihood:** High (rapid development)
- **Impact:** Medium (slows future development)
- **Mitigation:**
  - Document known debt in Week 8
  - Allocate 20% of Week 9-16 to refactoring
  - Code reviews for all PRs
  - Automated testing (unit + integration)

---

## Success Metrics by Phase

### **MVP (Week 8) Success Criteria:**
- [ ] 50 beta users onboarded
- [ ] 70% complete onboarding flow
- [ ] 500+ jobs scraped daily
- [ ] 200+ applications submitted
- [ ] <5% auto-apply failure rate
- [ ] 4.0+ user satisfaction score
- [ ] 50% weekly active user rate

### **Public Launch (Week 16) Success Criteria:**
- [ ] 1,000 signups
- [ ] 50 paying customers (5% conversion)
- [ ] ₹50K MRR
- [ ] 60% D7 retention
- [ ] Featured in 1 major publication (YourStory/Inc42)
- [ ] Product Hunt top 5 for the day
- [ ] 4.5+ rating (100+ reviews)

### **3-Month Post-Launch (Week 24) Success Criteria:**
- [ ] 10,000 total users
- [ ] 1,000 paying customers (10% conversion)
- [ ] ₹10L MRR
- [ ] 50% D30 retention
- [ ] 5,000+ job placements facilitated
- [ ] B2B pilot with 3 recruiting firms
- [ ] Break-even or profitable

---

## Dependencies & Prerequisites

### **External Dependencies:**
1. **WhatsApp Business API Approval** (Week 1)
   - Owner: Product Manager
   - Deadline: Week 1 Friday
   - Fallback: SMS via Twilio

2. **Claude API Access** (Week 2)
   - Owner: Backend Engineer
   - Deadline: Week 2 Monday
   - Fallback: OpenAI GPT-4

3. **Razorpay Account Setup** (Week 14)
   - Owner: Product Manager
   - Deadline: Week 14 Monday
   - Fallback: Stripe

4. **AWS Credits/Budget Approval** (Week 1)
   - Owner: Product Manager
   - Deadline: Week 1 Monday
   - Fallback: DigitalOcean

### **Internal Prerequisites:**
1. **Team Alignment on MVP Scope** (Before Week 1)
2. **Development Environment Setup** (Week 1 Day 1)
3. **Domain & Hosting Ready** (Week 1 Day 2)
4. **Beta User List Prepared** (Week 7)

---

## Weekly Standup Agenda

**Every Monday 10 AM:**
1. **Last Week Review** (15 min)
   - Completed tasks
   - Blockers encountered
   - Metrics update

2. **This Week Plan** (15 min)
   - Top 3 priorities
   - Who's doing what
   - Risks/dependencies

3. **Demo** (15 min)
   - Show working features
   - Get feedback

4. **Open Discussion** (15 min)
   - Technical decisions
   - Process improvements

**Total Duration:** 60 minutes

---

## Conclusion

This 16-week roadmap balances speed with quality, focusing on rapid iteration and user feedback. The MVP (Week 1-8) is intentionally lean, with only essential features needed to validate the core value proposition: WhatsApp-native job automation.

Phase 2 (Week 9-16) adds the monetization and differentiation features that make Jobsy a sustainable business. Post-launch, the focus shifts to scaling, community building, and capturing market share.

**Key Success Factors:**
1. **Ship weekly** - Maintain momentum with visible progress
2. **User feedback early** - Beta launch by Week 8, iterate based on real usage
3. **Ruthless prioritization** - Say no to nice-to-haves, focus on must-haves
4. **Quality automation** - Auto-apply must work reliably (>90% success rate)
5. **Clear value prop** - Users must see ROI in free tier to convert to paid

Let's build this! 🚀

---

**Roadmap Version:** 2.0  
**Last Updated:** April 9, 2026  
**Owner:** Santosh (Product Manager)  
**Contributors:** Claude (AI Assistant)
