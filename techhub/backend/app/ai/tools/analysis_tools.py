"""
数据分析工具 - 用于 AI 助手进行智能分析
Phase 2 核心工具：客户分析、趋势分析、智能推荐
"""
from datetime import datetime, timedelta
from collections import defaultdict
from app.ai.tools import register_tool, get_current_user
from app.models import Client, Contract, Project, Task, Ticket, PaymentRecord, User
from app import db


@register_tool(
    name="analyze_client_potential",
    description="分析客户的合作潜力，综合合同金额、合作频次、付款记录、工单响应等维度",
    parameters={
        "client_id": {
            "type": "integer",
            "description": "客户ID，不提供则分析所有客户",
            "required": False
        },
        "top_n": {
            "type": "integer",
            "description": "返回TOP N客户，默认5",
            "required": False
        }
    }
)
def analyze_client_potential(user_id=None, client_id=None, top_n=5):
    """分析客户合作潜力"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    six_months_ago = now - timedelta(days=180)
    one_year_ago = now - timedelta(days=365)
    
    if client_id:
        client = Client.query.get(client_id)
        if not client:
            return {"error": f"客户ID {client_id} 不存在"}
        clients = [client]
    else:
        clients = Client.query.filter(Client.status.in_(['active', 'potential'])).all()
    
    results = []
    for c in clients:
        # 1. 合同维度
        contracts = c.contracts.all()
        total_amount = sum(float(ct.amount) for ct in contracts if ct.amount)
        contract_count = len(contracts)
        active_contracts = [ct for ct in contracts if ct.status == 'active']
        
        # 2. 时间维度 - 最近合作活跃度
        recent_contracts = [ct for ct in contracts if ct.sign_date and ct.sign_date >= six_months_ago.date()]
        recent_amount = sum(float(ct.amount) for ct in recent_contracts if ct.amount)
        
        # 3. 付款维度
        payments = PaymentRecord.query.filter_by(client_id=c.id, payment_type="income", status="completed").all()
        total_paid = sum(float(p.amount) for p in payments if p.amount)
        payment_count = len(payments)
        
        # 4. 工单维度
        open_tickets = c.tickets.filter_by(status="open").count()
        resolved_tickets = c.tickets.filter_by(status="resolved").count()
        total_tickets = c.tickets.count()
        ticket_resolution_rate = round(resolved_tickets / total_tickets * 100, 1) if total_tickets > 0 else 100
        
        # 5. 项目维度
        projects = c.projects if c.projects else []
        project_count = len(projects)
        active_projects = [p for p in projects if p.status == 'active']
        
        # 6. 合作时长
        first_contract = min([ct.sign_date for ct in contracts if ct.sign_date], default=None)
        cooperation_days = (now.date() - first_contract).days if first_contract else 0
        
        # 计算综合得分 (0-100)
        # 合同金额得分 (最高30分)
        amount_score = min(30, (total_amount / 100000) * 10)
        
        # 合作频次得分 (最高15分)
        freq_score = min(15, contract_count * 3)
        
        # 活跃度得分 (最高20分)
        activity_score = 10 if recent_contracts else 0
        if recent_amount > 0:
            activity_score = min(20, 10 + (recent_amount / 50000) * 5)
        
        # 付款得分 (最高15分)
        payment_score = min(15, payment_count * 3)
        if total_paid > 0 and total_amount > 0:
            payment_ratio = total_paid / total_amount
            payment_score += min(5, payment_ratio * 5)
        
        # 稳定性得分 (最高10分)
        stability_score = max(0, 5 - open_tickets)
        if ticket_resolution_rate >= 80:
            stability_score += 5
        elif ticket_resolution_rate >= 50:
            stability_score += 2
        
        # 合作深度得分 (最高10分)
        depth_score = min(10, project_count * 2 + len(active_projects) * 3)
        
        total_score = amount_score + freq_score + activity_score + payment_score + stability_score + depth_score
        
        # 潜力评级
        if total_score >= 80:
            potential_level = "A+"
            potential_desc = "战略合作伙伴，重点维护"
        elif total_score >= 65:
            potential_level = "A"
            potential_desc = "高价值客户，深度挖掘"
        elif total_score >= 50:
            potential_level = "B+"
            potential_desc = "潜力客户，积极跟进"
        elif total_score >= 35:
            potential_level = "B"
            potential_desc = "普通客户，维持关系"
        else:
            potential_level = "C"
            potential_desc = "低活跃客户，需激活"
        
        results.append({
            "client_id": c.id,
            "client_name": c.name,
            "industry": c.industry,
            "level": c.level,
            "potential_level": potential_level,
            "potential_desc": potential_desc,
            "total_score": round(total_score, 1),
            "dimensions": {
                "contract_amount": {
                    "score": round(amount_score, 1),
                    "total_amount": total_amount,
                    "contract_count": contract_count,
                    "active_contracts": len(active_contracts)
                },
                "cooperation_frequency": {
                    "score": round(freq_score, 1),
                    "project_count": project_count,
                    "cooperation_days": cooperation_days
                },
                "recent_activity": {
                    "score": round(activity_score, 1),
                    "recent_contracts": len(recent_contracts),
                    "recent_amount": recent_amount
                },
                "payment_record": {
                    "score": round(payment_score, 1),
                    "total_paid": total_paid,
                    "payment_count": payment_count,
                    "payment_ratio": round(total_paid / total_amount, 2) if total_amount > 0 else 0
                },
                "stability": {
                    "score": round(stability_score, 1),
                    "open_tickets": open_tickets,
                    "total_tickets": total_tickets,
                    "resolution_rate": ticket_resolution_rate
                },
                "cooperation_depth": {
                    "score": round(depth_score, 1),
                    "project_count": project_count,
                    "active_projects": len(active_projects)
                }
            }
        })
    
    # 按得分排序
    results.sort(key=lambda x: x["total_score"], reverse=True)
    
    if client_id:
        return results[0] if results else {"error": "分析失败"}
    else:
        return {
            "total_clients": len(results),
            "top_clients": results[:top_n],
            "analysis_summary": {
                "a_plus_count": len([r for r in results if r["potential_level"] == "A+"]),
                "a_count": len([r for r in results if r["potential_level"] == "A"]),
                "b_plus_count": len([r for r in results if r["potential_level"] == "B+"]),
                "b_count": len([r for r in results if r["potential_level"] == "B"]),
                "c_count": len([r for r in results if r["potential_level"] == "C"])
            }
        }


@register_tool(
    name="analyze_client_trends",
    description="分析客户的合作趋势，包括合同金额变化、合作频次变化、付款趋势等",
    parameters={
        "client_id": {
            "type": "integer",
            "description": "客户ID",
            "required": True
        },
        "period": {
            "type": "string",
            "enum": ["3months", "6months", "1year", "2years"],
            "description": "分析周期，默认1年",
            "required": False
        }
    }
)
def analyze_client_trends(user_id=None, client_id=None, period="1year"):
    """分析客户合作趋势"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    client = Client.query.get(client_id)
    if not client:
        return {"error": f"客户ID {client_id} 不存在"}
    
    # 确定时间范围
    now = datetime.now()
    period_days = {"3months": 90, "6months": 180, "1year": 365, "2years": 730}
    days = period_days.get(period, 365)
    start_date = now - timedelta(days=days)
    
    # 按月统计合同金额
    contracts = Contract.query.filter(
        Contract.client_id == client_id,
        Contract.sign_date >= start_date.date()
    ).order_by(Contract.sign_date).all()
    
    monthly_data = defaultdict(lambda: {"contract_amount": 0, "contract_count": 0, "payment": 0})
    
    for ct in contracts:
        if ct.sign_date:
            month_key = ct.sign_date.strftime("%Y-%m")
            monthly_data[month_key]["contract_amount"] += float(ct.amount) if ct.amount else 0
            monthly_data[month_key]["contract_count"] += 1
    
    # 按月统计付款
    payments = PaymentRecord.query.filter(
        PaymentRecord.client_id == client_id,
        PaymentRecord.payment_type == "income",
        PaymentRecord.payment_date >= start_date.date()
    ).order_by(PaymentRecord.payment_date).all()
    
    for p in payments:
        if p.payment_date:
            month_key = p.payment_date.strftime("%Y-%m")
            monthly_data[month_key]["payment"] += float(p.amount) if p.amount else 0
    
    # 生成趋势数据
    trend_data = []
    for month in sorted(monthly_data.keys()):
        trend_data.append({
            "month": month,
            "contract_amount": round(monthly_data[month]["contract_amount"], 2),
            "contract_count": monthly_data[month]["contract_count"],
            "payment": round(monthly_data[month]["payment"], 2)
        })
    
    # 计算趋势指标
    if len(trend_data) >= 2:
        first_half = trend_data[:len(trend_data)//2]
        second_half = trend_data[len(trend_data)//2:]
        
        first_amount = sum(d["contract_amount"] for d in first_half)
        second_amount = sum(d["contract_amount"] for d in second_half)
        
        amount_trend = "上升" if second_amount > first_amount * 1.1 else ("下降" if second_amount < first_amount * 0.9 else "平稳")
        amount_change_rate = round((second_amount - first_amount) / first_amount * 100, 1) if first_amount > 0 else 0
    else:
        amount_trend = "数据不足"
        amount_change_rate = 0
    
    # 统计总览
    total_contract_amount = sum(d["contract_amount"] for d in trend_data)
    total_payment = sum(d["payment"] for d in trend_data)
    total_contracts = sum(d["contract_count"] for d in trend_data)
    
    return {
        "client_id": client.id,
        "client_name": client.name,
        "period": period,
        "period_days": days,
        "trend_summary": {
            "amount_trend": amount_trend,
            "amount_change_rate": amount_change_rate,
            "total_contract_amount": round(total_contract_amount, 2),
            "total_payment": round(total_payment, 2),
            "total_contracts": total_contracts,
            "avg_monthly_amount": round(total_contract_amount / max(len(trend_data), 1), 2)
        },
        "monthly_data": trend_data,
        "insights": [
            f"{'合作金额呈' + amount_trend + '趋势，变化幅度' + str(amount_change_rate) + '%' if amount_trend != '数据不足' else '数据量较少，暂无法判断趋势'}"
        ]
    }


@register_tool(
    name="recommend_clients_to_focus",
    description="智能推荐需要重点关注的客户，基于客户活跃度、逾期工单、待续签合同等",
    parameters={
        "focus_type": {
            "type": "string",
            "enum": ["renewal", "at_risk", "growth", "all"],
            "description": "关注类型：renewal待续签/at_risk流失风险/growth增长潜力/all全部",
            "required": False
        },
        "limit": {
            "type": "integer",
            "description": "返回数量，默认10",
            "required": False
        }
    }
)
def recommend_clients_to_focus(user_id=None, focus_type="all", limit=10):
    """智能推荐重点客户"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    now = datetime.now()
    three_months_later = now + timedelta(days=90)
    six_months_ago = now - timedelta(days=180)
    
    recommendations = []
    clients = Client.query.filter(Client.status.in_(['active', 'potential'])).all()
    
    for c in clients:
        reasons = []
        priority_score = 0
        
        # 1. 待续签合同（合同即将到期）
        expiring_contracts = Contract.query.filter(
            Contract.client_id == c.id,
            Contract.status == 'active',
            Contract.end_date <= three_months_later.date(),
            Contract.end_date >= now.date()
        ).all()
        
        if expiring_contracts:
            reasons.append(f"有 {len(expiring_contracts)} 份合同即将到期")
            priority_score += 30
        
        # 2. 流失风险（长期无新合同）
        recent_contracts = Contract.query.filter(
            Contract.client_id == c.id,
            Contract.sign_date >= six_months_ago.date()
        ).count()
        
        if recent_contracts == 0:
            total_contracts = Contract.query.filter_by(client_id=c.id).count()
            if total_contracts > 0:
                reasons.append("超过6个月无新合同，存在流失风险")
                priority_score += 25
        
        # 3. 未处理工单
        open_tickets = Ticket.query.filter_by(client_id=c.id, status='open').count()
        if open_tickets > 0:
            reasons.append(f"有 {open_tickets} 个未处理工单")
            priority_score += 15
        
        # 4. 高价值但活跃度下降
        total_amount = db.session.query(db.func.sum(Contract.amount)).filter_by(client_id=c.id).scalar() or 0
        if float(total_amount) > 500000 and recent_contracts == 0:
            reasons.append("高价值客户但近期无合作，需激活")
            priority_score += 20
        
        # 5. 近期有付款但未续签
        recent_payments = PaymentRecord.query.filter(
            PaymentRecord.client_id == c.id,
            PaymentRecord.payment_date >= six_months_ago.date()
        ).count()
        if recent_payments > 0 and not expiring_contracts:
            reasons.append("近期有付款记录，可推进续签")
            priority_score += 10
        
        if reasons:
            # 根据 focus_type 筛选
            if focus_type == "renewal" and not expiring_contracts:
                continue
            if focus_type == "at_risk" and recent_contracts > 0:
                continue
            if focus_type == "growth" and float(total_amount) < 100000:
                continue
            
            recommendations.append({
                "client_id": c.id,
                "client_name": c.name,
                "industry": c.industry,
                "level": c.level,
                "priority_score": priority_score,
                "reasons": reasons,
                "expiring_contracts": len(expiring_contracts) if expiring_contracts else 0,
                "open_tickets": open_tickets,
                "total_contract_amount": float(total_amount)
            })
    
    # 按优先级排序
    recommendations.sort(key=lambda x: x["priority_score"], reverse=True)
    
    return {
        "total": len(recommendations),
        "focus_type": focus_type,
        "recommendations": recommendations[:limit]
    }


@register_tool(
    name="analyze_project_progress",
    description="分析项目进度和健康度",
    parameters={
        "project_id": {
            "type": "integer",
            "description": "项目ID",
            "required": True
        }
    }
)
def analyze_project_progress(user_id=None, project_id=None):
    """分析项目进度"""
    user = get_current_user(user_id)
    if not user:
        return {"error": "用户未登录"}
    
    project = Project.query.get(project_id)
    if not project:
        return {"error": f"项目ID {project_id} 不存在"}
    
    now = datetime.now()
    stats = project.get_task_stats()
    
    total = stats["total"]
    done = stats["done"]
    in_progress = stats["in_progress"]
    todo = stats["todo"]
    progress = stats["progress"]
    
    # 时间进度
    time_progress = 0
    if project.start_date and project.end_date:
        start = project.start_date
        end = project.end_date
        if now.date() >= start:
            total_days = (end - start).days
            elapsed_days = (now.date() - start).days
            time_progress = min(100, round((elapsed_days / total_days) * 100, 1)) if total_days > 0 else 0
    
    # 健康度评估
    if time_progress > 0:
        if progress < time_progress - 20:
            health_status = "严重滞后"
            health_color = "red"
        elif progress < time_progress - 10:
            health_status = "轻度滞后"
            health_color = "orange"
        elif progress > time_progress + 10:
            health_status = "超前"
            health_color = "green"
        else:
            health_status = "正常"
            health_color = "blue"
    else:
        health_status = "未设置时间"
        health_color = "gray"
    
    # 即将到期的任务
    week_later = now + timedelta(days=7)
    upcoming_tasks = Task.query.filter_by(project_id=project_id).filter(
        Task.due_date <= week_later,
        Task.status != "done"
    ).order_by(Task.due_date.asc()).all()
    
    # 逾期任务
    overdue_tasks = Task.query.filter_by(project_id=project_id).filter(
        Task.due_date < now,
        Task.status != "done"
    ).all()
    
    # 成员工作量
    member_tasks = {}
    for task in project.tasks:
        if task.assignee_id:
            assignee_name = task.assignee.real_name or task.assignee.username
            if assignee_name not in member_tasks:
                member_tasks[assignee_name] = {"total": 0, "done": 0, "overdue": 0}
            member_tasks[assignee_name]["total"] += 1
            if task.status == "done":
                member_tasks[assignee_name]["done"] += 1
            if task.due_date and task.due_date < now:
                member_tasks[assignee_name]["overdue"] += 1
    
    return {
        "project_id": project.id,
        "project_name": project.name,
        "status": project.status,
        "progress": {
            "task_progress": progress,
            "time_progress": time_progress,
            "health_status": health_status,
            "health_color": health_color
        },
        "task_stats": stats,
        "upcoming_tasks": [{
            "id": t.id,
            "title": t.title,
            "assignee": t.assignee.real_name if t.assignee else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "priority": t.priority
        } for t in upcoming_tasks],
        "overdue_tasks": [{
            "id": t.id,
            "title": t.title,
            "assignee": t.assignee.real_name if t.assignee else None,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "days_overdue": (now.date() - t.due_date.date()).days if t.due_date else 0
        } for t in overdue_tasks],
        "member_workload": member_tasks
    }
