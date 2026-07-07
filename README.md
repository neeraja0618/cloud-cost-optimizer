# Cloud Cost Optimizer

A tool that detects idle AWS EC2 instances and helps reduce unnecessary cloud spend.

## What it does
- Monitors CPU utilization of EC2 instances over time
- Flags instances that stay idle below a usage threshold
- Estimates the cost being wasted by idle resources
- Automatically stops flagged idle instances
- Displays idle resources and potential savings on a dashboard

## Tech Stack
- Python (backend logic, cost analysis)
- AWS EC2 (target infrastructure)
- Streamlit (dashboard/UI)

## Team
Built as a team project (4 members) during a hackathon.

## Status
Prototype built for a hackathon — not production-ready.
