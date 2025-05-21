import { View, Text } from 'react-native'
import React from 'react'
import { Box } from './ui/box'
import { cn } from './ui/cn'
import { useTheme } from '@/utils/Themes/ThemeProvider'
import MyLinearGradient from './gradient/MyLinearGradient'

interface CardUpRoundedProps {
    children: React.ReactNode;
    variant?: 'background' | "card" | 'gradient';
    className?: string;
}
const CardUpRounded = ({ className, children, variant='background' }: CardUpRoundedProps) => {
    const { appliedTheme } = useTheme();
    const cnClassName = cn(`bg-${variant}-${appliedTheme} rounded-t-3xl -mt-10 flex-1 w-full p-5`, className);

    if(variant === 'gradient')
        return (
            <MyLinearGradient type='background' color={appliedTheme === 'dark' ? 'dark' : 'light-blue'} 
                className={cnClassName}>
                {children}
            </MyLinearGradient>
        )

    return (
        <Box className={cnClassName}>
            {children}
        </Box>
    )
}

export default CardUpRounded