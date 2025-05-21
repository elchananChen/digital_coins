export interface GooglePlace {
  place_id: string;
  description: string;
  structured_formatting: {
    main_text: string;
    secondary_text: string;
  };
}

export interface Address {
  place_id?: string | undefined;
  street: string | undefined;
  city: string | undefined;
  country: string | undefined;
  subpremise?: string | undefined;
  postal?: string | undefined;
  coords: coords | undefined;
}

export interface coords {
  lat: number;
  lng: number;
}

export interface SignupFinalDataType {
  address: Address;
  birthday: string | undefined;
  fName: string | undefined;
  lName: string | undefined;
  pass: string | undefined;
  phoneNumber: string | undefined;
  ssn: string | undefined;
}
