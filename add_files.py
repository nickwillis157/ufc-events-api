#!/usr/bin/env python3
import sys
import uuid

def generate_uuid():
    return str(uuid.uuid4()).replace('-', '').upper()[:24]

# Read the project file
project_file = "/Users/nick/UFC Scraper/UFC_Events_iOS/UFC_Events_iOS.xcodeproj/project.pbxproj"

with open(project_file, 'r') as f:
    content = f.read()

# Generate UUIDs for the new files
content_view_uuid = generate_uuid()
event_list_view_uuid = generate_uuid()
event_detail_view_uuid = generate_uuid()
sample_data_uuid = generate_uuid()

content_view_build_uuid = generate_uuid()
event_list_view_build_uuid = generate_uuid()
event_detail_view_build_uuid = generate_uuid()
sample_data_build_uuid = generate_uuid()

# Add PBXBuildFile entries
build_file_section = "/* Begin PBXBuildFile section */"
new_build_files = f"""{build_file_section}
\t\t{content_view_build_uuid} /* ContentView.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {content_view_uuid} /* ContentView.swift */; }};
\t\t{event_list_view_build_uuid} /* EventListView.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {event_list_view_uuid} /* EventListView.swift */; }};
\t\t{event_detail_view_build_uuid} /* EventDetailView.swift in Sources */ = {{isa = PBXBuildFile; fileRef = {event_detail_view_uuid} /* EventDetailView.swift */; }};
\t\t{sample_data_build_uuid} /* UFC_SampleData.json in Resources */ = {{isa = PBXBuildFile; fileRef = {sample_data_uuid} /* UFC_SampleData.json */; }};"""

content = content.replace(build_file_section, new_build_files)

# Add PBXFileReference entries
file_ref_section = "/* Begin PBXFileReference section */"
new_file_refs = f"""{file_ref_section}
\t\t{content_view_uuid} /* ContentView.swift */ = {{isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.swift; path = ContentView.swift; sourceTree = "<group>"; }};
\t\t{event_list_view_uuid} /* EventListView.swift */ = {{isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.swift; path = EventListView.swift; sourceTree = "<group>"; }};
\t\t{event_detail_view_uuid} /* EventDetailView.swift */ = {{isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = sourcecode.swift; path = EventDetailView.swift; sourceTree = "<group>"; }};
\t\t{sample_data_uuid} /* UFC_SampleData.json */ = {{isa = PBXFileReference; fileEncoding = 4; lastKnownFileType = text.json; path = UFC_SampleData.json; sourceTree = "<group>"; }};"""

content = content.replace(file_ref_section, new_file_refs)

# Add to UFC_Events_iOS group
group_children = """\t\t\t\tchildren = (
\t\t\t\t\t01279D432E17BA4800521A68 /* UFC_Events_iOSApp.swift */,
\t\t\t\t\t{content_view_uuid} /* ContentView.swift */,
\t\t\t\t\t{event_list_view_uuid} /* EventListView.swift */,
\t\t\t\t\t{event_detail_view_uuid} /* EventDetailView.swift */,
\t\t\t\t\t013665E32E1873F8005B4EFA /* EventCardView.swift */,
\t\t\t\t\t013665E12E1873F8005B4EFA /* FightSegmentView.swift */,
\t\t\t\t\t013665E22E1873F8005B4EFA /* FilterView.swift */,
\t\t\t\t\t013665E02E1873F8005B4EFA /* UFCEvent.swift */,
\t\t\t\t\t01279D472E17BA4900521A68 /* Assets.xcassets */,
\t\t\t\t\t01279D492E17BA4900521A68 /* Preview Content */,
\t\t\t\t\t{sample_data_uuid} /* UFC_SampleData.json */,""".format(
    content_view_uuid=content_view_uuid,
    event_list_view_uuid=event_list_view_uuid,
    event_detail_view_uuid=event_detail_view_uuid,
    sample_data_uuid=sample_data_uuid
)

old_group_children = """\t\t\tchildren = (
\t\t\t\t01279D432E17BA4800521A68 /* UFC_Events_iOSApp.swift */,
\t\t\t\t013665E32E1873F8005B4EFA /* EventCardView.swift */,
\t\t\t\t013665E12E1873F8005B4EFA /* FightSegmentView.swift */,
\t\t\t\t013665E22E1873F8005B4EFA /* FilterView.swift */,
\t\t\t\t013665E02E1873F8005B4EFA /* UFCEvent.swift */,
\t\t\t\t01279D472E17BA4900521A68 /* Assets.xcassets */,
\t\t\t\t01279D492E17BA4900521A68 /* Preview Content */,"""

content = content.replace(old_group_children, group_children)

# Add to Sources build phase
sources_files = f"""\t\t\tfiles = (
\t\t\t\t013665E62E1873F8005B4EFA /* FilterView.swift in Sources */,
\t\t\t\t01279D442E17BA4800521A68 /* UFC_Events_iOSApp.swift in Sources */,
\t\t\t\t{content_view_build_uuid} /* ContentView.swift in Sources */,
\t\t\t\t{event_list_view_build_uuid} /* EventListView.swift in Sources */,
\t\t\t\t{event_detail_view_build_uuid} /* EventDetailView.swift in Sources */,
\t\t\t\t013665E52E1873F8005B4EFA /* FightSegmentView.swift in Sources */,
\t\t\t\t013665E42E1873F8005B4EFA /* UFCEvent.swift in Sources */,
\t\t\t\t013665E72E1873F8005B4EFA /* EventCardView.swift in Sources */,"""

old_sources_files = """\t\t\tfiles = (
\t\t\t\t013665E62E1873F8005B4EFA /* FilterView.swift in Sources */,
\t\t\t\t01279D442E17BA4800521A68 /* UFC_Events_iOSApp.swift in Sources */,
\t\t\t\t013665E52E1873F8005B4EFA /* FightSegmentView.swift in Sources */,
\t\t\t\t013665E42E1873F8005B4EFA /* UFCEvent.swift in Sources */,
\t\t\t\t013665E72E1873F8005B4EFA /* EventCardView.swift in Sources */,"""

content = content.replace(old_sources_files, sources_files)

# Add to Resources build phase
resources_files = f"""\t\t\tfiles = (
\t\t\t\t01279D4B2E17BA4900521A68 /* Preview Assets.xcassets in Resources */,
\t\t\t\t01279D482E17BA4900521A68 /* Assets.xcassets in Resources */,
\t\t\t\t{sample_data_build_uuid} /* UFC_SampleData.json in Resources */,"""

old_resources_files = """\t\t\tfiles = (
\t\t\t\t01279D4B2E17BA4900521A68 /* Preview Assets.xcassets in Resources */,
\t\t\t\t01279D482E17BA4900521A68 /* Assets.xcassets in Resources */,"""

content = content.replace(old_resources_files, resources_files)

# Write the updated project file
with open(project_file, 'w') as f:
    f.write(content)

print("Successfully added missing files to Xcode project!")
print("Files added:")
print("- ContentView.swift")
print("- EventListView.swift") 
print("- EventDetailView.swift")
print("- UFC_SampleData.json")