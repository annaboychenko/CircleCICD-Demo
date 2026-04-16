from reporting import ReportManager

report_manager = ReportManager()

print("========== PAMS REPORTING DASHBOARD ==========\n")

print("1. OCCUPANCY BY CITY")
for item in report_manager.get_occupancy_by_city():
    print(
        f"{item['location']}: "
        f"Total={item['total_apartments']}, "
        f"Occupied={item['occupied']}, "
        f"Vacant={item['vacant']}, "
        f"Rate={item['occupancy_rate']}%"
    )

print("\n2. OCCUPANCY FOR ONE CITY (Bristol)")
print(report_manager.get_occupancy_for_city("Bristol"))

print("\n3. OCCUPANCY BY APARTMENT")
for item in report_manager.get_occupancy_by_apartment():
    print(item)

print("\n4. FINANCIAL SUMMARY")
financial = report_manager.get_financial_summary()
print(financial)

print("\n5. MAINTENANCE SUMMARY")
maintenance = report_manager.get_maintenance_summary()
print(maintenance)

print("\n6. MAINTENANCE COSTS BY CITY")
for item in report_manager.get_maintenance_costs_by_city():
    print(item)

print("\n7. MAINTENANCE COSTS FOR ONE CITY (London)")
print(report_manager.get_maintenance_costs_for_city("London"))

print("\n8. MAINTENANCE COSTS FOR ONE APARTMENT (1)")
print(report_manager.get_maintenance_costs_for_apartment(1))

print("\n9. FULL REPORT")
print(report_manager.generate_full_report())