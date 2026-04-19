from reporting import ReportManager

report_manager = ReportManager()

print("=== OCCUPANCY BY CITY ===")
for item in report_manager.get_occupancy_by_city():
    print(item)

print("\n=== OCCUPANCY BY APARTMENT ===")
for item in report_manager.get_occupancy_by_apartment():
    print(item)

print("\n=== FINANCIAL SUMMARY ===")
print(report_manager.get_financial_summary())

print("\n=== MAINTENANCE SUMMARY ===")
print(report_manager.get_maintenance_summary())

print("\n=== MAINTENANCE COSTS BY CITY ===")
for item in report_manager.get_maintenance_costs_by_city():
    print(item)