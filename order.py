from dataclasses import dataclass, field

@dataclass
class Order:
    accession: str
    body_parts: list
    modality: str
    study_description: str
    image_count: int
    ffs_body_part_count: int = field(init=False)
    fee: int = field(init=False, default=0)

    def __post_init__(self):
        if self.modality == 'CT':
            self.body_parts = [x for x in self.body_parts if x not in (
                'CSPINE',
                'TSPINE',
                'LSPINE',
                'PELVIS',
                'KUB',
                'KIDNEYS',
                'ADRENALS',
                  # 'PANCREAS',

            )]
        self.ffs_body_part_count = len(self.body_parts)
        if self.ffs_body_part_count == 0:
            if self.image_count:
                # warn(f"Assuming 1 body part for {self.accession} ({self.study_description})")
                self.ffs_body_part_count = 1
            # else:
            #     warn(f"No images for {self.accession} ({self.study_description})")
        if self.ffs_body_part_count:
            match(self.modality):
                case 'CT':
                    match self.ffs_body_part_count:
                        case 1:
                            self.fee = 60
                        case 2:
                            self.fee = 135
                        case 3:
                            self.fee = 160
                        case _:
                            self.fee = 200
                            self.ffs_body_part_count = 4
                case 'MR':
                    self.fee = 75
                    self.ffs_body_part_count = 1
                case 'CR':
                    match self.ffs_body_part_count:
                        case 1:
                            self.fee = 12
                        case 2:
                            self.fee = 20
                        case _:
                            self.fee = 35
                            self.ffs_body_part_count = 3
                case 'US':
                    self.fee = 12
                    self.ffs_body_part_count = 1
                case _:
                    raise Exception(f'Illegal state: modality = {self.modality}')

    def __str__(self):
        return f"{self.modality}x{self.ffs_body_part_count} = ${self.fee} ({self.accession})"
    
    @staticmethod
    def dict_from(response):
        if not response['success']:
            raise Exception('Server error')
        orders = {}
        for data in response['result']:
            procedure = data['mRequestedProcedureList'][0]
            if (modality := procedure['mNormalizedModality']) not in ('CT','CR','MR','US'):
                continue
            order = Order(
                data['mAccessionNumber'],
                data['mBodyPartList'],
                modality,
                procedure['mStudyDescription'],
                procedure['mRemoteImageCount'],
                )
            orders[order.accession] = order
        return orders
