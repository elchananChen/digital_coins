import { NavigationProp, ParamListBase } from '@react-navigation/native';
import { Address } from './other';

export type Props = {
  navigation: TNavigation;
  route?: any;
};

export type TNavigation = NavigationProp<ParamListBase>;

export type signUpInputs =
  | 'fName'
  | 'lName'
  | 'birthday'
  | 'ssn'
  | 'api'
  | 'pass'
  | 'address'
  | 'phoneNumber'
  | 'phonePrefix'
  | 'email';

export type SignUpScreensProps = {
  handleScreenChange: (newScreenStep: 'back' | 'next' | string, fromEdit?: boolean) => void;
  formHook: {
    values: {
      phonePrefix: string;
      phoneNumber: string;
      email: string;
      pass: string;
      address: Address;
      fName: string;
      lName: string;
      birthday: string;
      ssn: string;
      api: string;
    };
    errors: Record<signUpInputs, string>;
    handleInputChange: (field: signUpInputs, val: string | boolean | Address | null) => void;
    setErrorByFields: (errors: Partial<Record<signUpInputs, string>>) => void;
    setErrors: React.Dispatch<React.SetStateAction<Record<signUpInputs, string>>>;
  };
};

export type idVerifyTypes = 'ID Card' | "Driver's License" | 'Passport' | 'Selfie' | null;

export type idVerifyProps = {
  handleScreenChange: (newScreenStep: 'back' | 'next' | string, data?: any) => void;
  finalData?: {
    type: idVerifyTypes;
    frontIdPhoto: string;
    backIdPhoto: string;
    isGov: boolean;
    isSelfie: boolean;
  };
};

export type TTheme = 'light' | 'dark';
