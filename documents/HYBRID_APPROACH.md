# 🎯 Hybrid Approach: GSD + Direct Development

**Created:** 2026-03-21  
**Version:** 1.0  
**For:** OpenClaw Trading Agents Project

---

## 📋 Overview

ใช้ **GSD Workflow** สำหรับส่วนที่เหมาะสม และ **Direct Development** สำหรับส่วนที่สำคัญ

```
┌─────────────────────────────────────────────────────────┐
│              Trading Agents Architecture                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  🟢 GSD Workflow (Velocity)                             │
│  ├── Dashboard UI                                       │
│  ├── Alert Modals                                       │
│  ├── Database Schema (SQLite)                           │
│  ├── Documentation                                      │
│  └── Test Templates                                     │
│                                                         │
│  🟡 Opencode Direct (Balanced)                          │
│  ├── Agent Orchestration Logic                          │
│  ├── API Integration (Hyperliquid)                      │
│  ├── Config Management                                  │
│  └── Monitoring & Logging                               │
│                                                         │
│  🔴 Hand-Coded (Precision & Safety)                     │
│  ├── Trading Strategy (Supertrend)                      │
│  ├── Risk Calculations                                  │
│  ├── Execution Validation (Slippage, Liquidity)         │
│  └── Security & Authentication                          │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 🎯 Decision Matrix

### เมื่อไหร่ใช้วิธีไหน?

| Component | GSD | Direct | Hand-Code | เหตุผล |
|-----------|-----|--------|-----------|--------|
| **Dashboard UI** | ✅ | ⚠️ | ❌ | UI/UX ชัดเจน, ไม่ซับซ้อน |
| **Alert Modals** | ✅ | ⚠️ | ❌ | Boilerplate, standard patterns |
| **Database Schema** | ✅ | ⚠️ | ❌ | Structure ชัดเจนจาก spec |
| **Documentation** | ✅ | ⚠️ | ❌ | GSD ทำได้เร็ว |
| **Test Templates** | ✅ | ⚠️ | ❌ | Boilerplate code |
| **Agent Orchestration** | ⚠️ | ✅ | ❌ | Logic ปานกลาง ต้องควบคุมบ้าง |
| **API Integration** | ⚠️ | ✅ | ❌ | ต้อง handle errors, retries |
| **Config Management** | ⚠️ | ✅ | ❌ | ต้อง validate, secure |
| **Monitoring/Logging** | ⚠️ | ✅ | ❌ | ต้อง customize |
| **Trading Strategy** | ❌ | ⚠️ | ✅ | Core logic, ต้องแม่นยำ 100% |
| **Risk Calculations** | ❌ | ⚠️ | ✅ | Safety-critical |
| **Execution Validation** | ❌ | ⚠️ | ✅ | Slippage, liquidity checks |
| **Security/Auth** | ❌ | ⚠️ | ✅ | Security-critical |

---

## 🏗️ Architecture by Approach

### 🟢 GSD Workflow Components

```
Trading Agents - GSD Parts
├── Dashboard UI
│   ├── Portfolio overview modal
│   ├── Trade history table
│   ├── Performance charts (layout)
│   └── Settings panel
│
├── Alert System
│   ├── Telegram alert templates
│   ├── Toast notifications
│   └── Alert configuration UI
│
├── Database
│   ├── SQLite schema (state.db)
│   ├── Table definitions
│   └── Index creation
│
├── Documentation
│   ├── README.md
│   ├── API_REFS.md
│   └── SETUP_GUIDE.md
│
└── Tests
    ├── Test templates
    └── Integration test scaffolding
```

**GSD Commands:**
```bash
/gsd:plan
"สร้าง [component] ตาม [spec]

Golden Rules:
- Tech Stack: [stack]
- Data: [method]
- Constraints: [list]

แตก task เป็น atomic tasks (≤ 10 นาที)"
```

---

### 🟡 Opencode Direct Components

```
Trading Agents - Direct Opencode Parts
├── Agent Orchestration
│   ├── Scanner → Sentiment → Strategy flow
│   ├── Parallel execution logic
│   └── Error handling & retries
│
├── API Integration
│   ├── Hyperliquid API wrapper
│   ├── Rate limiting
│   └── Response parsing
│
├── Config Management
│   ├── Config loading & validation
│   ├── Environment variables
│   └── Secrets management
│
└── Monitoring
    ├── Health check logic
    ├── Logging setup
    └── Metrics collection
```

**Opencode Commands:**
```bash
opencode

# Implement ด้วย control สูง
"สร้าง [component] ตาม [spec]

Requirements:
- [requirement 1]
- [requirement 2]

ต้อง handle:
- [error case 1]
- [error case 2]

เขียน code ให้ดูง่าย มี comments"
```

---

### 🔴 Hand-Coded Components

```
Trading Agents - Hand-Coded Parts
├── Trading Strategy
│   ├── Supertrend calculation
│   ├── Signal generation logic
│   └── Parameter optimization
│
├── Risk Management
│   ├── Position sizing (Kelly, Fixed Fractional)
│   ├── Daily loss tracking
│   ├── Exposure limits
│   └── Circuit breakers
│
├── Execution Validation
│   ├── Slippage calculation
│   ├── Liquidity checks
│   ├── Order validation
│   └── Fill tracking
│
└── Security
    ├── API key encryption
    ├── Authentication
    └── Audit logging
```

**Why Hand-Code:**
- Core business logic (ต้องแม่นยำ 100%)
- Safety-critical (risk, execution)
- Security-sensitive (keys, auth)
- Performance-critical (low-latency)

---

## 📊 Workflow Comparison

### GSD Workflow

```
Phase 0: Golden Rules
    ↓
Phase 1: Plan → Check GSF_PLAN.md → Approve
    ↓
Phase 2: Build → Track STATE.md → Intervene
    ↓
Phase 3: Verify → GSD + Your Test → Done

Time: 10-30 นาที per feature
Control: Low-Medium
Quality: Medium-High
Best For: UI, Boilerplate, Docs
```

---

### Direct Opencode

```
Step 1: Open Opencode
    ↓
Step 2: Send Detailed Prompt
    ↓
Step 3: Review Code (Iterate if needed)
    ↓
Step 4: Test & Verify

Time: 5-15 นาที per feature
Control: Medium-High
Quality: High
Best For: Logic, Integration, Config
```

---

### Hand-Coded

```
Step 1: Design & Plan
    ↓
Step 2: Write Code
    ↓
Step 3: Unit Test
    ↓
Step 4: Integration Test
    ↓
Step 5: Code Review (Self/Peer)

Time: 30-120 นาที per feature
Control: Maximum
Quality: Maximum
Best For: Core Logic, Security, Risk
```

---

## 🎯 Implementation Plan

### Week 1: Foundation (GSD + Direct)

| Day | Component | Approach | Time |
|-----|-----------|----------|------|
| 1 | Project Structure | GSD | 30 min |
| 1 | SQLite Schema | GSD | 20 min |
| 2 | Config Module | Direct | 45 min |
| 2 | Database Wrapper | Direct | 45 min |
| 3 | Scanner Agent (UI) | GSD | 30 min |
| 3 | Scanner Agent (Logic) | Hand | 60 min |
| 4 | Sentiment Agent | Direct | 60 min |
| 4 | Strategy Agent | Hand | 90 min |
| 5 | Risk Agent | Hand | 90 min |

---

### Week 2: Integration (Direct + Hand)

| Day | Component | Approach | Time |
|-----|-----------|----------|------|
| 6 | Execution Agent | Hand | 90 min |
| 6 | Hyperliquid API | Direct | 60 min |
| 7 | Agent Orchestration | Direct | 90 min |
| 7 | Error Handling | Direct | 45 min |
| 8 | Dashboard UI | GSD | 60 min |
| 8 | Alert System | GSD | 45 min |
| 9 | Monitoring | Direct | 60 min |
| 9 | Logging | Direct | 45 min |
| 10 | Integration Test | Direct | 90 min |

---

### Week 3: Testing & Safety (All Approaches)

| Day | Component | Approach | Time |
|-----|-----------|----------|------|
| 11 | Unit Tests | GSD | 60 min |
| 11 | Integration Tests | Direct | 90 min |
| 12 | Paper Trading | Hand | 120 min |
| 12 | Circuit Breakers | Hand | 60 min |
| 13 | Documentation | GSD | 60 min |
| 13 | Security Audit | Hand | 90 min |
| 14 | Performance Test | Direct | 90 min |

---

### Week 4: Deployment (Direct + Hand)

| Day | Component | Approach | Time |
|-----|-----------|----------|------|
| 15 | Environment Setup | Direct | 60 min |
| 15 | API Keys Config | Hand | 30 min |
| 16 | Testnet Deploy | Direct | 90 min |
| 16 | Health Checks | Direct | 45 min |
| 17 | Soft Launch | Direct | 60 min |
| 17 | Monitor & Fix | Direct | 120 min |
| 18 | Optimization | Hand | 90 min |
| 18 | Final Review | All | 60 min |

---

## 📋 Templates

### GSD Prompt Template

```markdown
Implement [Component] ตาม [Spec File]

Golden Rules:
- Tech Stack: [stack]
- Data Persistence: [method]
- Constraints:
  - [constraint 1]
  - [constraint 2]
- Source of Truth: [spec path]

Atomic Tasks:
1. [task 1] (5-10 min)
2. [task 2] (5-10 min)
3. [task 3] (5-10 min)

สร้าง planning files:
- GSF_PLAN.md
- GSF_STATE.md
```

---

### Direct Opencode Prompt Template

```markdown
สร้าง [Component] สำหรับ Trading Agents

Requirements:
1. [requirement 1]
2. [requirement 2]
3. [requirement 3]

Must Handle:
- [error case 1]
- [error case 2]
- [edge case]

Tech Stack:
- [language/framework]
- [dependencies allowed]

Code Style:
- Clean, readable
- Comments สำหรับ complex logic
- Error handling ครบ

ไฟล์ที่เกี่ยวข้อง:
- [file 1]
- [file 2]
```

---

### Hand-Code Planning Template

```markdown
# Hand-Code Plan: [Component]

## Purpose
[ทำไมต้องเขียนเอง]

## Requirements
- [req 1]
- [req 2]

## Design
[algorithm/design]

## Implementation Steps
1. [step 1]
2. [step 2]
3. [step 3]

## Testing
- [ ] Unit test 1
- [ ] Unit test 2
- [ ] Integration test

## Security Review
- [ ] Input validation
- [ ] Error handling
- [ ] Audit logging
```

---

## 🔧 Tool Selection

### By Component Type

| Component | Tool | Why |
|-----------|------|-----|
| **UI Components** | GSD | Fast, standard patterns |
| **Database Schema** | GSD | Structure ชัดเจน |
| **Documentation** | GSD | Quick, comprehensive |
| **Agent Logic** | Direct | Need control, not too complex |
| **API Integration** | Direct | Handle errors, retries |
| **Trading Strategy** | Hand | Core logic, must be perfect |
| **Risk Management** | Hand | Safety-critical |
| **Security** | Hand | Security-critical |

---

## 📊 Quality Gates

### GSD Components

```
Quality Checklist:
- [ ] GSF_PLAN.md created
- [ ] GSF_STATE.md updated
- [ ] Atomic tasks ≤ 10 min
- [ ] GSD self-verify passed
- [ ] Integration test passed
- [ ] Code reviewed
```

---

### Direct Components

```
Quality Checklist:
- [ ] Requirements clear
- [ ] Error handling complete
- [ ] Code reviewed
- [ ] Unit tests written
- [ ] Integration test passed
```

---

### Hand-Coded Components

```
Quality Checklist:
- [ ] Design documented
- [ ] Code reviewed (peer)
- [ ] Unit tests (≥ 80% coverage)
- [ ] Integration tests passed
- [ ] Security review passed
- [ ] Performance tested
```

---

## 🚨 When to Switch Approach

### GSD → Direct

**Switch when:**
- Tasks consistently > 15 min
- Code quality not meeting standards
- Too many iterations needed
- Requirements unclear

**How to switch:**
```
หยุด GSD ก่อน
สรุปสิ่งที่ทำไปแล้ว
เปลี่ยนเป็น Direct Opencode
เขียน prompt ที่ชัดเจนกว่า
```

---

### Direct → Hand

**Switch when:**
- Bug ที่ซับซ้อน
- Performance issues
- Security concerns
- Core logic ไม่ถูกต้อง

**How to switch:**
```
หยุด Direct
Review code ที่มี
เขียนใหม่เอง (hand-code)
Test อย่างละเอียด
```

---

## 📈 Metrics & KPIs

### Track Per Component

| Metric | GSD | Direct | Hand |
|--------|-----|--------|------|
| **Dev Time** | 10-30 min | 5-15 min | 30-120 min |
| **Bug Rate** | Medium | Low | Very Low |
| **Code Quality** | Medium-High | High | Very High |
| **Control** | Low-Medium | Medium-High | Maximum |
| **Best For** | UI, Docs | Logic, Integration | Core, Security |

---

### Project-Level Metrics

```
Target:
- GSD Components: 30% (fast delivery)
- Direct Components: 40% (balanced)
- Hand-Coded: 30% (critical parts)

Quality Goals:
- Bug Rate: < 5% in production
- Test Coverage: ≥ 80%
- Security Issues: 0
- Performance: < 1s latency (non-trading)
```

---

## 🎓 Lessons Learned

### From Sudoku Testing

**✅ What Worked:**
- GSD สร้าง planning files (GSF_PLAN.md, GSF_STATE.md)
- Atomic tasks ช่วยให้เห็น progress
- Double-layer verify จับ bug ได้

**⚠️ What Didn't:**
- GSD ไม่ได้ใช้เสมอไป (ต้อง enforce)
- Task ยังใหญ่เกินไปบ้าง
- Planning files อ่านยาก

**💡 Improvements:**
- Enforce planning files creation
- Break tasks smaller (≤ 10 min)
- Better templates for planning

---

## 🎯 Summary

```
┌─────────────────────────────────────────────┐
│         Hybrid Approach Summary             │
├─────────────────────────────────────────────┤
│                                             │
│  Use the Right Tool for the Right Job:      │
│                                             │
│  🟢 GSD     → UI, Boilerplate, Docs         │
│  🟡 Direct  → Logic, Integration, Config    │
│  🔴 Hand    → Core, Risk, Security          │
│                                             │
│  Benefits:                                  │
│  ✓ Speed (GSD for fast parts)               │
│  ✓ Control (Direct for medium parts)        │
│  ✓ Safety (Hand for critical parts)         │
│                                             │
│  Result: Best of All Worlds!                │
│                                             │
└─────────────────────────────────────────────┘
```

---

**Last Updated:** 2026-03-21  
**Version:** 1.0  
**Next Review:** After Week 1 implementation
