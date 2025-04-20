from dataclasses import dataclass, field
from datetime import datetime
import re
from order import Order

@dataclass
class FFSprofile:
    study_count: int
    studies: dict[str,list[int]]
    fee: int

@dataclass
class Reporter:
    first_name: str
    last_name: str
    reports: list[tuple[str,datetime]] = field(default_factory=list)
    ffsProfile: FFSprofile | None = None

    @staticmethod
    def fromCommaSeparated(commaSeparated: str):
        result = re.split(r",\s*", commaSeparated, maxsplit=1)
        return Reporter(result[1] if len(result) > 1 else '', result[0])

    def setFFS(self, orders: dict[str, Order]):
        study_count = 0
        studies = dict(CR=[0,0,0],CT=[0,0,0,0],MR=[0],US=[0])
        fee = 0
        for (accession,modified) in self.reports:
            try: order = orders[accession]
            except KeyError: continue
            if order.modality in studies and order.ffs_body_part_count:
                study_count += 1
                fee += order.fee
                studies[order.modality][order.ffs_body_part_count-1] += 1
        if study_count:
            self.ffsProfile = FFSprofile(study_count, studies, fee)
    
    def print(self, orders: dict[str, Order], print_individual_orders: bool):
        print(f'\n{self.first_name} {self.last_name}')
        order_counts: dict[str,int] = {}
        for (accession, _) in self.reports:
            modality = orders[accession].modality
            try:
                order_counts[modality] += 1
            except KeyError:
                order_counts[modality] = 1
        print(f'Studies: {len(self.reports)} ({', '.join([f'{modality}: {count}' for modality, count in sorted(order_counts.items())])})')
        if self.ffsProfile:
            print("FFS: ${:,d} ({} studies)".format(self.ffsProfile.fee, self.ffsProfile.study_count))
            for modality, body_part_counts in self.ffsProfile.studies.items():
                count = 0
                for i, body_part_count in enumerate(body_part_counts):
                    if body_part_count:
                        count += body_part_count
                if count:
                    s = f'{modality}: {count}'
                    if len(self.ffsProfile.studies[modality]) > 1:
                        s += f' ({', '.join([f"{body_part_count} x {i+1}p" for i, body_part_count in enumerate(body_part_counts) if body_part_count])})'
                    print(s)
        if print_individual_orders:
            for (accession, modified) in self.reports:
                print(f"{orders[accession]} on {modified.strftime('%a %d %b %Y, %H:%M')}")

def unique_accessions(reports: list[Reporter]):
    return {report[0] for reporter in reports for report in reporter.reports}

def ffs_reports(reports: list[Reporter], orders: dict[str, Order]):
    for reporter in reports:
        reporter.setFFS(orders)
    return sorted([reporter for reporter in reports if reporter.ffsProfile], key=lambda x:x.ffsProfile.fee, reverse=False)
